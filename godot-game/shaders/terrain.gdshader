shader_type spatial;
// Terrain material (docs/terrain_textures.md section 4). Works in the Compatibility renderer.
// - All 28 ground textures in one Texture2DArray, layer order from terrain_textures.md section 2.
// - UV from world position: xz / 4 (one 128 px tile = 4 m = 32 px per metre). Steep rock uses the dominant
//   axis projection (triplanar without blending, so pixels stay crisp).
// - Biome: worked out from the warped depth "s" in UV.x. Inside a border only the two strongest biomes are
//   considered and a per-pixel dither on the 32 px per metre grid picks one, so borders blend in pixel steps.
// - Inside a biome the layer rules from terrain_textures.md section 4.2 pick base, patches, litter, wet,
//   high ground, scree, special patches, steep rock and paths.
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
uniform float near_cut = 0.0;   // far terrain mesh: hide it close to the camera, where the detailed chunks are
uniform float far_drop = 0.0;   // far terrain mesh sits slightly lower so the detailed chunks always win

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
	float d = hash(px * 0.0137 + 3.1);         // per pixel dither
	float d2 = hash(px * 0.0071 + 9.7);
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
		// height based dither: grass blades poke over the neighbour instead of a soft fade
		b = 1 + (d < w ? j : i);
		border = 1.0 - smoothstep(0.0, 60.0, min(f, band_depth - f));
	}
	vec4 m = texture(mask_map, (wpos.xz - mask_rect.xy) / mask_rect.zw);
	float slope = 1.0 - clamp(wnrm.y, 0.0, 1.0);
	float n = vnoise(wpos.xz / 14.0) * 0.65 + vnoise(wpos.xz / 5.0) * 0.35;

	int layer = r_base[b];
	if (r_patch[b] >= 0 && n + border * border_patch[b] * 0.55 + (d2 - 0.5) * 0.1 > patch_threshold[b]) layer = r_patch[b];
	if (r_litter[b] >= 0 && m.a > 0.3 + d2 * 0.45) layer = r_litter[b];
	if (r_wet[b] >= 0 && m.g > d) layer = r_wet[b];
	if (r_high[b] >= 0 && wpos.y + (d - 0.5) * 5.0 > high_y[b]) layer = r_high[b];
	if (r_special[b] >= 0 && m.b > d) layer = r_special[b];
	if (r_mid[b] >= 0 && slope + (d2 - 0.5) * 0.08 > mid_slope[b]) layer = r_mid[b];
	bool steep = slope + (d - 0.5) * 0.06 > steep_slope[b];
	if (r_path[b] >= 0 && m.r > d * 0.8 + 0.1) {
		layer = r_path[b];
		steep = false;
	}
	vec3 col = tri_sample(float(steep ? r_steep[b] : layer));
	ALBEDO = col;
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
}
