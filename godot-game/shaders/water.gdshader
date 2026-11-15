shader_type spatial;
// Stylised water for the Compatibility renderer and web builds (no depth texture, no refraction).
// Depth comes from depth_map (level - terrain height, 2 px per metre, built in game_world.gd _make_water):
// 4 shallow-to-deep colour bands, scrolling shore foam, fade to clear at the shoreline, gentle vertex
// waves and toon sparkles. Everything is snapped to the 32 px per metre grid.
// flow > 0 turns it into the waterfall ribbon (game_world.gd _make_waterfall): UV is metres across / down the
// surface, UV2 is (metres to the bottom end, flow travel), where travel grows slowly on the flat and fast on the
// face, so the ripples and white streaks scroll down the fall at a speed that follows its steepness.
// foam_only: the foam disc on the plunge pool (white noise, radial falloff).
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
uniform vec2 rect_size = vec2(0.0);    // the true rect size (m): still water fades out in its last 0.75 m
uniform float ribbon_width = 9.0;      // waterfall: u runs 0..ribbon_width, soft 0.5 m edges
uniform bool foam_only = false;

varying vec3 wpos;
varying vec2 lpos;
varying vec2 flow_uv;

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
	flow_uv = UV2;
	if (flow <= 0.0) {
		vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
		VERTEX.y += (sin(w.x * 0.9 + TIME * 1.3) + sin(w.z * 1.1 - TIME * 1.1)) * 0.5 * wave_height;
	}
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 grid = floor((flow > 0.0 ? UV : wpos.xz) * 32.0) / 32.0;
	vec2 drift = vec2(TIME * 0.15, TIME * 0.09);
	float r = vnoise(grid * 1.6 + drift) * 0.6 + vnoise(grid * 4.0 - drift * 1.7) * 0.4;

	if (foam_only) {
		float fn = vnoise(grid * 3.0 + vec2(TIME * 0.8, -TIME * 0.6));
		float fall = 1.0 - smoothstep(0.35, 1.0, length(lpos) / 3.5 + (fn - 0.5) * 0.3);
		ALBEDO = foam_color.rgb;
		ALPHA = fall * (0.45 + 0.4 * step(0.5, fn));
	} else if (flow > 0.0) {
		// down the fall: grid.x metres across, travel snapped to the same 32 px per metre grid
		float tv = floor(flow_uv.y * 32.0) / 32.0;
		float rf = vnoise(vec2(grid.x * 1.6, tv * 1.6 - TIME * flow)) * 0.6 + vnoise(vec2(grid.x * 4.0, tv * 4.0 - TIME * flow * 1.7)) * 0.4;
		float band = floor(rf * 4.0) / 4.0;
		vec3 col = deep_color.rgb * (0.82 + band * 0.32);
		float streak = vnoise(vec2(grid.x * 3.0, tv * 0.6 - TIME * flow));
		col = mix(col, foam_color.rgb, step(0.6, streak) * 0.7);
		col = mix(col, foam_color.rgb, step(0.62, rf) * 0.35);
		ALBEDO = col;
		float edge = smoothstep(0.0, 0.5, UV.x) * smoothstep(0.0, 0.5, ribbon_width - UV.x);
		float ends = smoothstep(0.0, 1.0, UV.y) * smoothstep(0.0, 1.0, flow_uv.x);
		ALPHA = 0.92 * edge * ends;
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
		// and fade out over the last 0.75 m inside the rect, so no plane can show a straight cut line
		if (rect_size.x > 0.0) {
			vec2 a = wpos.xz - rect.xy;
			float de = min(min(a.x, rect_size.x - a.x), min(a.y, rect_size.y - a.y));
			ALPHA *= smoothstep(0.0, 0.75, de);
		}
	}
	ROUGHNESS = 0.18;
	METALLIC = 0.0;
}
