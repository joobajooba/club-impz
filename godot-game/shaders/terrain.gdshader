shader_type spatial;
// Terrain material (docs/terrain_textures.md section 4). Works in the Compatibility renderer.
// - All 31 ground textures in one Texture2DArray, layer order from terrain_textures.md section 2 (the three
//   smooth cliff_stone layers appended at 28 to 30).
// - UV from world position: xz / 4 (one 256 px tile = 4 m = 64 px per metre). Slopes use the dominant axis
//   projection only (no blending of two projections, which smeared and doubled the pixels); the seams between
//   projections are broken up on the pixel grid.
// - Biome: worked out from the warped depth "s" in UV.x. Inside a border only the two strongest biomes are
//   considered and a clumped dither on the 64 px per metre grid picks one, so borders blend in pixel steps.
// - Inside a biome the layer rules from terrain_textures.md section 4.2 pick base, patches, litter, wet,
//   high ground, scree, special patches, steep rock and paths. Layer edges use the clumped dither too, so they
//   read as clean, ragged edges instead of salt-and-pepper speckle.
// - Outside the world's border (the skirt's cliffs and mountains): steep ground is the biome's smooth cliff stone and
//   ground above cap_y its cap layer (snow).
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
uniform int r_cliff[6];
uniform int r_cap[6];
uniform float patch_threshold[6];
uniform float steep_slope[6];
uniform float mid_slope[6];
uniform float high_y[6];
uniform float border_patch[6];
uniform float special_on_steep[6];  // 1: steep cells in the special patch use the special layer (forest waterfall cliff)
uniform float cap_y[6];
uniform float near_cut = 0.0;   // far terrain mesh: hide it close to the camera, where the detailed chunks are
uniform float far_drop = 0.0;   // far terrain mesh sits slightly lower so the detailed chunks always win
uniform vec4 detail_rect = vec4(-1e6, -1e6, 1e6, 1e6);  // x0, z0, x1, z1: where detailed chunks exist
uniform float px_per_m = 64.0;  // texel density of the layers (256 px over 4 m)

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

bool in_detail(vec2 p) {
	return p.x >= detail_rect.x && p.y >= detail_rect.y && p.x <= detail_rect.z && p.y <= detail_rect.w;
}

bool deep_in_detail(vec2 p) {
	// strictly inside: far mesh vertices on the edge of the detailed chunks keep their height, so the two meshes
	// meet there with no groove
	return p.x > detail_rect.x + 0.5 && p.y > detail_rect.y + 0.5 && p.x < detail_rect.z - 0.5 && p.y < detail_rect.w - 0.5;
}

void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	// only where detailed chunks cover it: out on the skirt the far mesh is the ground itself
	if (deep_in_detail(w.xz)) {
		VERTEX.y -= far_drop;
	}
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	sdepth = UV.x;
}

// one sample from the dominant axis projection at 64 px per metre, so slopes don't stretch and pixels stay crisp
vec3 tri_sample(float layer, float jit) {
	vec3 a = abs(wnrm);
	a.y += 0.08;                   // flat-ish ground keeps the top projection
	a += (jit - 0.5) * 0.12;       // ragged, pixel stepped seams between projections
	if (a.y >= a.x && a.y >= a.z) {
		return texture(layers, vec3(wpos.xz / 4.0, layer)).rgb;
	}
	if (a.x >= a.z) {
		return texture(layers, vec3(wpos.zy / 4.0, layer)).rgb;
	}
	return texture(layers, vec3(wpos.xy / 4.0, layer)).rgb;
}

// ordered dither on the texel grid: a 4x4 Bayer matrix ((i + 0.5) / 16), shifted per 4x4 block by a slow hash so
// the pattern never shows its repeat (J00BA, 2026-11-15: gradual texture blending)
float bayer4(vec2 p) {
	const float B[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
	vec2 shift = floor(vec2(hash(floor(p / 4.0) * 0.173), hash(floor(p / 4.0) * 0.311 + 5.7)) * 4.0);
	ivec2 q = ivec2(mod(p + shift, 4.0));
	return (B[q.y * 4 + q.x] + 0.5) / 16.0;
}

float lum(vec3 c) {
	return dot(c, vec3(0.3, 0.59, 0.11));
}

// two-layer blending: every rule is a soft weight; a full weight replaces both layers, a partial one collapses the
// result so far to its dominant layer (under) and blends the rule's layer over it with that weight
void apply_rule(inout int under, inout int over, inout float w_over, int lay, float w) {
	if (lay < 0 || w <= 0.0) {
		return;
	}
	if (w >= 0.999) {
		under = lay;
		over = lay;
		w_over = 0.0;
		return;
	}
	under = (w_over >= 0.5) ? over : under;
	over = lay;
	w_over = w;
}

// the height blend: each texel's height is its brightness, so the incoming layer's tall bright texels (blade tips,
// stones) poke through first; pixel steps keep the art crisp, a little colour mix mid-band makes the fade gradual
vec3 height_blend(vec3 cu, vec3 co, float w, float dither) {
	float ha = lum(cu) + (1.0 - w);
	float hb = lum(co) + w;
	float pick = clamp((hb - ha) / 0.35 + 0.5 + (dither - 0.5) * 0.6, 0.0, 1.0);
	vec3 col = mix(cu, co, step(0.5, pick));
	return mix(col, mix(cu, co, w), 0.35 * (1.0 - abs(2.0 * w - 1.0)));
}

void fragment() {
	if (near_cut > 0.0 && in_detail(wpos.xz) && distance(wpos, CAMERA_POSITION_WORLD) < near_cut) {
		discard;
	}
	vec2 px = floor(wpos.xz * px_per_m);       // the texel grid
	float bayer = bayer4(px);
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
		if (w > 0.0) {
			// pick the biome per texel with the same Bayer + height trick, on each biome's base layer
			float bi = float(r_base[1 + i]);
			float bj = float(r_base[1 + j]);
			float ha = lum(tri_sample(bi, bayer)) + (1.0 - w);
			float hb = lum(tri_sample(bj, bayer)) + w;
			if (clamp((hb - ha) / 0.35 + 0.5 + (bayer - 0.5) * 0.6, 0.0, 1.0) >= 0.5) {
				b = 1 + j;
			}
		}
		border = 1.0 - smoothstep(0.0, 60.0, min(f, band_depth - f));
	}
	vec2 muv = (wpos.xz - mask_rect.xy) / mask_rect.zw;
	bool outside = muv.x < 0.0 || muv.y < 0.0 || muv.x > 1.0 || muv.y > 1.0;
	vec4 m = outside ? vec4(0.0) : texture(mask_map, muv);
	float slope = 1.0 - clamp(wnrm.y, 0.0, 1.0);
	float n = (vnoise(wpos.xz / 14.0) * 0.65 + vnoise(wpos.xz / 5.0) * 0.35 + vnoise(wpos.xz / 2.0) * 0.15) / 1.15;

	// every rule is a soft weight over a few metres, in the old order and with the old override meaning
	int under = r_base[b];
	int over = under;
	float w_over = 0.0;
	if (r_patch[b] >= 0) {
		float thr = patch_threshold[b];
		apply_rule(under, over, w_over, r_patch[b], smoothstep(thr - 0.12, thr + 0.12, n + border * border_patch[b] * 0.55));
	}
	apply_rule(under, over, w_over, r_litter[b], smoothstep(0.25, 0.75, m.a));
	apply_rule(under, over, w_over, r_wet[b], smoothstep(0.1, 0.7, m.g));
	if (r_high[b] >= 0) {
		apply_rule(under, over, w_over, r_high[b], smoothstep(high_y[b] - 3.0, high_y[b] + 3.0, wpos.y + (n - 0.5) * 3.0));
	}
	float special_w = r_special[b] >= 0 ? smoothstep(0.1, 0.7, m.b) : 0.0;
	apply_rule(under, over, w_over, r_special[b], special_w);
	apply_rule(under, over, w_over, r_mid[b], smoothstep(mid_slope[b] - 0.06, mid_slope[b] + 0.06, slope));
	float steep_w = smoothstep(steep_slope[b] - 0.05, steep_slope[b] + 0.05, slope);
	float path_w = r_path[b] >= 0 ? smoothstep(0.15, 0.6, m.r) : 0.0;
	apply_rule(under, over, w_over, r_path[b], path_w);
	steep_w *= 1.0 - path_w;                    // the path clears the steep layer where it wins
	int steep_layer = (special_w > 0.5 && special_on_steep[b] > 0.5) ? r_special[b] : r_steep[b];
	if (outside) {
		// the skirt: rock cliffs, a snow (or grass) cap up high
		if (r_cap[b] >= 0) {
			apply_rule(under, over, w_over, r_cap[b], smoothstep(cap_y[b] - 3.0, cap_y[b] + 3.0, wpos.y + n * 6.0));
		}
		if (r_cliff[b] >= 0) {
			steep_layer = r_cliff[b];
			steep_w = smoothstep(0.19, 0.29, slope);
		}
	}
	apply_rule(under, over, w_over, steep_layer, steep_w);

	// at most two layer samples: one for flat single-layer ground, two only inside a transition
	vec3 col = tri_sample(float(under), bayer);
	if (w_over > 0.0 && over != under) {
		vec3 co = tri_sample(float(over), bayer);
		col = w_over >= 0.999 ? co : height_blend(col, co, w_over, bayer);
	}
	// gentle large scale light and dark so wide fields and cliff faces don't look flat or visibly tiled;
	// cliffs also get faint horizontal strata
	col *= 0.92 + 0.16 * (vnoise(wpos.xz / 23.0) * 0.6 + vnoise(wpos.xz / 7.0) * 0.4);
	if (steep_w > 0.0) {
		// cliff faces: broad bedding layers a few metres tall and big light and dark sweeps across the face,
		// in world space, so the smooth stone never shows its 4 m repeat
		float along = (wpos.x + wpos.z);
		float strata = 0.9 + 0.16 * vnoise(vec2(along / 14.0, wpos.y / 3.5)) + 0.08 * vnoise(vec2(along / 40.0, wpos.y / 16.0));
		col *= mix(1.0, strata, steep_w);
	}
	ALBEDO = col;
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
}
