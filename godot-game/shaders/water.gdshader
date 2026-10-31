shader_type spatial;
// Water (game_worlds.md section 4.8 water colours). Flat plane, gentle pixel ripples snapped to the
// 32 px per metre grid, soft transparency. No screen space refraction, so it works in web builds.
// flow > 0 turns it into a falling sheet (waterfall): ripples scroll down the plane's local y.
render_mode blend_mix, depth_draw_opaque, cull_disabled, diffuse_lambert, specular_schlick_ggx;

uniform vec4 water_color : source_color = vec4(0.23, 0.6, 0.85, 1.0);
uniform vec4 foam_color : source_color = vec4(0.85, 0.95, 1.0, 1.0);
uniform float alpha = 0.8;
uniform float flow = 0.0;

varying vec3 wpos;
varying vec2 lpos;

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
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	lpos = VERTEX.xz;
}

void fragment() {
	vec2 grid = floor((flow > 0.0 ? vec2(lpos.x, lpos.y) : wpos.xz) * 32.0) / 32.0;
	vec2 drift = flow > 0.0 ? vec2(0.0, -TIME * flow) : vec2(TIME * 0.15, TIME * 0.09);
	float r = vnoise(grid * 1.6 + drift) * 0.6 + vnoise(grid * 4.0 - drift * 1.7) * 0.4;
	float band = floor(r * 4.0) / 4.0;                 // stepped, pixel art bands
	vec3 col = water_color.rgb * (0.82 + band * 0.32);
	float hi = step(0.86, r);
	if (flow > 0.0) hi = step(0.62, r);
	col = mix(col, foam_color.rgb, hi * 0.55);
	ALBEDO = col;
	ALPHA = flow > 0.0 ? 0.92 : alpha;
	ROUGHNESS = 0.18;
	METALLIC = 0.0;
}
