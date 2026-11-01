shader_type spatial;
// Stylised water for the Compatibility renderer and web builds (no depth texture, no refraction).
// Depth comes from depth_map (level - terrain height, 2 px per metre, built in game_world.gd _make_water):
// 4 shallow-to-deep colour bands, scrolling shore foam, fade to clear at the shoreline, gentle vertex
// waves and toon sparkles. Everything is snapped to the 32 px per metre grid.
// flow > 0 turns it into a falling sheet (waterfall): ripples scroll down the plane's local y.
render_mode blend_mix, depth_draw_opaque, cull_disabled, diffuse_lambert, specular_schlick_ggx;

uniform vec4 shallow_color : source_color = vec4(0.45, 0.82, 0.86, 1.0);
uniform vec4 deep_color : source_color = vec4(0.23, 0.6, 0.85, 1.0);
uniform vec4 foam_color : source_color = vec4(0.9, 0.97, 1.0, 1.0);
uniform float alpha = 0.85;
uniform float flow = 0.0;
uniform float wave_height = 0.03;
uniform float deep_depth = 1.5;         // depth (m) where the deepest band starts
uniform sampler2D depth_map : filter_linear, repeat_disable;
uniform vec4 rect = vec4(0.0, 0.0, 1.0, 1.0);  // x0, z0, width, depth of depth_map in world metres
uniform bool use_depth = false;

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
	lpos = VERTEX.xz;
	if (flow <= 0.0) {
		vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
		VERTEX.y += (sin(w.x * 0.9 + TIME * 1.3) + sin(w.z * 1.1 - TIME * 1.1)) * 0.5 * wave_height;
	}
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 grid = floor((flow > 0.0 ? lpos : wpos.xz) * 32.0) / 32.0;
	vec2 drift = flow > 0.0 ? vec2(0.0, -TIME * flow) : vec2(TIME * 0.15, TIME * 0.09);
	float r = vnoise(grid * 1.6 + drift) * 0.6 + vnoise(grid * 4.0 - drift * 1.7) * 0.4;

	if (flow > 0.0) {
		float band = floor(r * 4.0) / 4.0;
		vec3 col = deep_color.rgb * (0.82 + band * 0.32);
		col = mix(col, foam_color.rgb, step(0.62, r) * 0.55);
		ALBEDO = col;
		ALPHA = 0.92;
	} else {
		// smooth world coords (not the pixel grid) so the shoreline follows the terrain, not 2 m steps
		float depth = use_depth ? texture(depth_map, (wpos.xz - rect.xy) / rect.zw).r : deep_depth;
		float t = smoothstep(0.0, deep_depth, depth);
		vec3 col = mix(shallow_color.rgb, deep_color.rgb, t);
		col *= 0.95 + floor(r * 4.0) / 4.0 * 0.1;                // stepped ripple shading, half strength
		// shore foam: a soft scrolling band in the shallows, not a hard white outline
		float fn = vnoise(grid * 3.0 + vec2(TIME * 0.4, -TIME * 0.3));
		float foam = (1.0 - smoothstep(0.04, 0.28, depth + (fn - 0.5) * 0.1)) * 0.5;
		col = mix(col, foam_color.rgb, foam);
		// toon sparkles: bright pixels where the noise peaks, more of them at grazing view angles
		float graze = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
		float sp = step(0.965 - graze * 0.12, vnoise(grid * 6.0 + vec2(TIME * 0.7, TIME * 0.5))) * (1.0 - foam);
		col = mix(col, vec3(1.0), sp * 0.8);
		EMISSION = vec3(sp * 0.2);
		ALBEDO = col;
		// soft fade to clear at the waterline: hides the 2 m triangle edge where the plane meets the terrain
		ALPHA = alpha * smoothstep(0.0, 0.22, depth);
	}
	ROUGHNESS = 0.18;
	METALLIC = 0.0;
}
