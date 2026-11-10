shader_type spatial;
// Terrain material (docs/terrain_textures.md section 4). Works in the Compatibility renderer.
// - All 28 ground textures in one Texture2DArray, layer order from terrain_textures.md section 2.
// - UV from world position: xz / 4 (one 128 px tile = 4 m = 32 px per metre). Steep rock uses the dominant
//   axis projection (triplanar without blending, so pixels stay crisp).
// - Biome: worked out from the warped depth "s" in UV.x. Inside a border only the two strongest biomes are
//   considered; a smoothstep weight over blend_half, an ordered (Bayer) dither and each biome's base texel
//   brightness pick one per pixel, so borders blend in pixel steps with no grain.
// - Inside a biome the layer rules from terrain_textures.md section 4.2 (base, patches, litter, wet, high
//   ground, scree, special patches, paths, steep rock) are soft weights. Two layers are carried, under and
//   over: a height blend lets the brighter texels of the incoming layer poke through first, and in the
//   middle of a transition the two colours are also mixed a little (both nearest sampled on the same texel
//   grid, so every pixel stays crisp).
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_lambert, specular_disabled;

uniform sampler2DArray layers : source_color, filter_nearest_mipmap_anisotropic, repeat_enable;
uniform sampler2D mask_map : filter_linear, repeat_disable;
uniform vec4 mask_rect = vec4(0.0, -256.0, 1280.0, 512.0);
uniform int fixed_biome = -1;
uniform float band_depth = 256.0;
uniform float blend_half = 22.5;
uniform int r_base[6];
uniform int r_patch[6];
uniform int r_litter[6];
uniform int r_steep[6];
uniform int r_mid[6];
uniform int r_high[6];
uniform int r_wet[6];
uniform int r_special[6];
uniform int r_path[6];
uniform float patch_threshold[6];
uniform float steep_slope[6];
uniform float mid_slope[6];
uniform float high_y[6];
uniform float border_patch[6];
uniform float special_on_steep[6];  // 1: steep cells in the special patch use the special layer (forest waterfall cliff)
uniform float near_cut = 0.0;   // far terrain mesh: hide it close to the camera, where the detailed chunks are
uniform float far_drop = 0.0;   // far terrain mesh sits slightly lower so the detailed chunks always win

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

varying vec3 wpos;
varying vec3 wnrm;
varying float sdepth;

float hash(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

float lum(vec3 c) {
	return dot(c, vec3(0.3, 0.59, 0.11));
}

// one layer rule with weight w: full weight replaces both layers; a partial weight collapses the current
// blend to its dominant layer, which becomes under, and the rule layer becomes over
void add_rule(int layer, float w, inout int under, inout int over, inout float w_over) {
	if (layer < 0 || w <= 0.0) {
		return;
	}
	if (w >= 0.999) {
		under = layer;
		over = layer;
		w_over = 0.0;
		return;
	}
	under = w_over >= 0.5 ? over : under;
	over = layer;
	w_over = w;
}

// the brighter (taller) texels of over poke through first; returns the over share 0 or 1 for this pixel
float height_pick(vec3 a, vec3 b, float w, float bayer) {
	float ha = lum(a) + (1.0 - w);
	float hb = lum(b) + w;
	return step(0.5, clamp((hb - ha) / 0.35 + 0.5 + (bayer - 0.5) * 0.6, 0.0, 1.0));
}

void vertex() {
	VERTEX.y -= far_drop;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	sdepth = UV.x;
}

// triplanar sample at 32 px per metre (one 128 px tile = 4 m), so slopes don't stretch
vec3 tri_sample(float layer) {
	if (wnrm.y > 0.97) {
		return texture(layers, vec3(wpos.xz / 4.0, layer)).rgb;  // flat ground: one sample
	}
	vec3 w = pow(abs(wnrm), vec3(8.0));
	w /= (w.x + w.y + w.z);
	return texture(layers, vec3(wpos.zy / 4.0, layer)).rgb * w.x
		+ texture(layers, vec3(wpos.xz / 4.0, layer)).rgb * w.y
		+ texture(layers, vec3(wpos.xy / 4.0, layer)).rgb * w.z;
}

void fragment() {
	if (near_cut > 0.0 && distance(wpos, CAMERA_POSITION_WORLD) < near_cut) {
		discard;
	}
	vec2 px = floor(wpos.xz * 32.0);           // the 32 px per metre grid
	// ordered dither: 4 x 4 Bayer, shifted per 4 x 4 block by a hash so the pattern doesn't repeat visibly
	vec2 blk = floor(px / 4.0);
	vec2 bo = floor(vec2(hash(blk * 0.37 + 1.7), hash(blk * 0.53 + 5.3)) * 4.0);
	ivec2 bi = ivec2(mod(px + bo, 4.0));
	float bayer = (BAYER[bi.y * 4 + bi.x] + 0.5) / 16.0;
	int b = fixed_biome;
	float border = 0.0;
	if (b < 0) {
		float band = sdepth / band_depth;
		int i = clamp(int(floor(band)), 0, 4);
		float f = sdepth - float(i) * band_depth;
		int j = i;
		float w = 0.0;
		if (f > band_depth - blend_half && i < 4) {
			j = i + 1;
			w = (f - (band_depth - blend_half)) / (2.0 * blend_half);
		} else if (f < blend_half && i > 0) {
			j = i - 1;
			w = (blend_half - f) / (2.0 * blend_half);
		}
		w = smoothstep(0.0, 1.0, w);
		b = 1 + i;
		if (j != i && w > 0.0) {
			// height based pick on the two base layers: grass blades poke over the neighbour in pixel steps
			vec3 ci = tri_sample(float(r_base[1 + i]));
			vec3 cj = tri_sample(float(r_base[1 + j]));
			if (height_pick(ci, cj, w, bayer) > 0.5) {
				b = 1 + j;
			}
		}
		border = 1.0 - smoothstep(0.0, 60.0, min(f, band_depth - f));
	}
	vec4 m = texture(mask_map, (wpos.xz - mask_rect.xy) / mask_rect.zw);
	float slope = 1.0 - clamp(wnrm.y, 0.0, 1.0);
	float n = (vnoise(wpos.xz / 14.0) * 0.65 + vnoise(wpos.xz / 5.0) * 0.35 + vnoise(wpos.xz / 2.0) * 0.15) / 1.15;

	// soft rule weights, in the rule order of section 4.2 (later rules override earlier ones)
	int under = r_base[b];
	int over = under;
	float w_over = 0.0;
	float thr = patch_threshold[b];
	add_rule(r_patch[b], smoothstep(thr - 0.12, thr + 0.12, n + border * border_patch[b] * 0.55), under, over, w_over);
	add_rule(r_litter[b], smoothstep(0.25, 0.75, m.a), under, over, w_over);
	add_rule(r_wet[b], smoothstep(0.1, 0.7, m.g), under, over, w_over);
	add_rule(r_high[b], smoothstep(high_y[b] - 3.0, high_y[b] + 3.0, wpos.y + (n - 0.5) * 3.0), under, over, w_over);
	float w_special = r_special[b] >= 0 ? smoothstep(0.1, 0.7, m.b) : 0.0;
	add_rule(r_special[b], w_special, under, over, w_over);
	add_rule(r_mid[b], smoothstep(mid_slope[b] - 0.06, mid_slope[b] + 0.06, slope), under, over, w_over);
	float w_path = r_path[b] >= 0 ? smoothstep(0.15, 0.6, m.r) : 0.0;
	add_rule(r_path[b], w_path, under, over, w_over);
	// paths clear steep rock where they win
	float w_steep = smoothstep(steep_slope[b] - 0.05, steep_slope[b] + 0.05, slope) * (1.0 - w_path);
	int steep_layer = (w_special >= 0.5 && special_on_steep[b] > 0.5) ? r_special[b] : r_steep[b];
	add_rule(steep_layer, w_steep, under, over, w_over);

	vec3 col = tri_sample(float(under));
	if (w_over > 0.0 && w_over < 1.0) {
		vec3 oc = tri_sample(float(over));
		vec3 stepped = mix(col, oc, height_pick(col, oc, w_over, bayer));
		// colour mix, strongest (35%) in the middle of the band and zero at both ends
		col = mix(stepped, mix(col, oc, w_over), 0.35 * (1.0 - abs(2.0 * w_over - 1.0)));
	}
	ALBEDO = col;
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
}
