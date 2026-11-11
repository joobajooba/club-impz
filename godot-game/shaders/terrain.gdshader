shader_type spatial;
// Terrain material (docs/terrain_textures.md section 4). Works in the Compatibility renderer.
// - All 28 ground textures in one Texture2DArray, layer order from terrain_textures.md section 2.
// - UV from world position: xz / 4 (one 256 px tile = 4 m = 64 px per metre). Slopes use the dominant axis
//   projection only (no blending of two projections, which smeared and doubled the pixels); the seams between
//   projections are broken up on the pixel grid.
// - Biome: worked out from the warped depth "s" in UV.x. Inside a border only the two strongest biomes are
//   considered and a clumped dither on the 64 px per metre grid picks one, so borders blend in pixel steps.
// - Inside a biome the layer rules from terrain_textures.md section 4.2 pick base, patches, litter, wet,
//   high ground, scree, special patches, steep rock and paths. Layer edges use the clumped dither too, so they
//   read as clean, ragged edges instead of salt-and-pepper speckle.
// - Outside the world's border (the skirt's cliffs and mountains): steep ground is the biome's cliff rock and
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

void fragment() {
	if (near_cut > 0.0 && in_detail(wpos.xz) && distance(wpos, CAMERA_POSITION_WORLD) < near_cut) {
		discard;
	}
	vec2 px = floor(wpos.xz * px_per_m);       // the texel grid
	// clumped dither: mostly smooth noise a few texels across with a little per texel grain, so layer and biome
	// edges are ragged lines of whole texel clumps rather than scattered single pixels
	float d = clamp(vnoise(px / 6.0) * 0.75 + vnoise(px / 2.0) * 0.15 + hash(px * 0.0137 + 3.1) * 0.1, 0.0, 1.0);
	float d2 = clamp(vnoise(px / 5.0 + 17.0) * 0.8 + hash(px * 0.0071 + 9.7) * 0.2, 0.0, 1.0);
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
		// grass blades poke over the neighbour in clumps instead of a soft fade
		float bd = clamp(vnoise(wpos.xz * 0.9) * 0.6 + d * 0.4, 0.0, 1.0);
		b = 1 + (bd < w ? j : i);
		border = 1.0 - smoothstep(0.0, 60.0, min(f, band_depth - f));
	}
	vec2 muv = (wpos.xz - mask_rect.xy) / mask_rect.zw;
	bool outside = muv.x < 0.0 || muv.y < 0.0 || muv.x > 1.0 || muv.y > 1.0;
	vec4 m = outside ? vec4(0.0) : texture(mask_map, muv);
	float slope = 1.0 - clamp(wnrm.y, 0.0, 1.0);
	float n = vnoise(wpos.xz / 14.0) * 0.65 + vnoise(wpos.xz / 5.0) * 0.35;

	int layer = r_base[b];
	if (r_patch[b] >= 0 && n + border * border_patch[b] * 0.55 + (d2 - 0.5) * 0.1 > patch_threshold[b]) layer = r_patch[b];
	// mask layers: a clean edge on the mask's smooth contour, ragged by a few texels only (no speckle bleeding)
	if (r_litter[b] >= 0 && m.a > 0.5 + (d2 - 0.5) * 0.2) layer = r_litter[b];
	if (r_wet[b] >= 0 && m.g > 0.5 + (d - 0.5) * 0.2) layer = r_wet[b];
	if (r_high[b] >= 0 && wpos.y + (d - 0.5) * 5.0 > high_y[b]) layer = r_high[b];
	bool special_here = r_special[b] >= 0 && m.b > 0.5 + (d - 0.5) * 0.2;
	if (special_here) layer = r_special[b];
	if (r_mid[b] >= 0 && slope + (d2 - 0.5) * 0.08 > mid_slope[b]) layer = r_mid[b];
	bool steep = slope + (d - 0.5) * 0.06 > steep_slope[b];
	if (r_path[b] >= 0 && m.r > 0.5 + (d - 0.5) * 0.25) {
		layer = r_path[b];
		steep = false;
	}
	int steep_layer = (special_here && special_on_steep[b] > 0.5) ? r_special[b] : r_steep[b];
	if (outside) {
		// the skirt: rock cliffs, a snow (or grass) cap up high
		if (r_cap[b] >= 0 && wpos.y + (d - 0.5) * 8.0 + n * 6.0 > cap_y[b]) layer = r_cap[b];
		if (r_cliff[b] >= 0) {
			steep_layer = r_cliff[b];
			steep = slope + (d - 0.5) * 0.06 > 0.24;
		}
	}
	vec3 col = tri_sample(float(steep ? steep_layer : layer), d2);
	// gentle large scale light and dark so wide fields and cliff faces don't look flat or visibly tiled;
	// cliffs also get faint horizontal strata
	col *= 0.92 + 0.16 * (vnoise(wpos.xz / 23.0) * 0.6 + vnoise(wpos.xz / 7.0) * 0.4);
	if (steep) {
		col *= 0.86 + 0.24 * vnoise(vec2((wpos.x + wpos.z) / 9.0, wpos.y / 2.2));
	}
	ALBEDO = col;
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
}
