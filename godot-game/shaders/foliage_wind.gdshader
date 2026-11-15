shader_type spatial;
// Wind for trees and foliage (blockbench_detailed_prompts.md section 3.4.5, game_worlds.md section 4.9).
// Card bases stay still, tips move most (sway grows with height above the model's base).
// Also: hard alpha (discard), nearest pixels, a gradient map recolour so one plant shape serves several biomes
// (game_worlds.md section 4.10), a petal recolour for placeholder flowers, and a shrink-out fade at the view edge.
render_mode cull_disabled, depth_draw_opaque, diffuse_lambert, specular_disabled;

uniform sampler2D albedo_tex : source_color, filter_nearest_mipmap, repeat_disable;
uniform float wind_strength = 0.6;     // 0 = still (trunks); biome wind multiplies this
uniform float sway_height = 1.0;       // height (m) where the sway reaches full strength
uniform float fade_start = 44.0;
uniform float fade_end = 54.0;
uniform float recolor = 0.0;           // 0..1: map luminance onto recolor_dark -> recolor_light
uniform vec4 recolor_dark : source_color = vec4(0.2, 0.3, 0.1, 1.0);
uniform vec4 recolor_light : source_color = vec4(0.6, 0.8, 0.3, 1.0);
uniform float petal = 0.0;             // 1 = recolour strongly red pixels (rose petals) to petal_color
uniform vec4 petal_color : source_color = vec4(0.4, 0.5, 0.9, 1.0);
uniform vec4 tint : source_color = vec4(1.0);

void vertex() {
	vec3 origin = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float h = max(VERTEX.y, 0.0);
	float phase = origin.x * 0.21 + origin.z * 0.17;
	float gust = sin(TIME * 0.6 + origin.x * 0.02) * 0.5 + 0.5;
	float sway = sin(TIME * 1.8 + phase) * 0.7 + sin(TIME * 3.3 + phase * 1.7) * 0.3;
	float bend = wind_strength * (0.6 + gust * 0.6) * pow(h / max(sway_height, 0.01), 1.6) * 0.09;
	VERTEX.x += sway * bend;
	VERTEX.z += sway * bend * 0.6;
	float dist = distance(origin, INV_VIEW_MATRIX[3].xyz);
	VERTEX *= 1.0 - smoothstep(fade_start, fade_end, dist);
}

void fragment() {
	vec4 c = texture(albedo_tex, UV);
	if (c.a < 0.5) {
		discard;
	}
	vec3 col = c.rgb;
	if (recolor > 0.0) {
		float l = clamp(dot(col, vec3(0.3, 0.59, 0.11)) * 1.7 - 0.1, 0.0, 1.0);
		col = mix(col, mix(recolor_dark.rgb, recolor_light.rgb, l), recolor);
	}
	if (petal > 0.0 && c.r > c.g * 1.5 && c.r > c.b * 1.5) {
		float l = clamp(c.r * 1.3, 0.0, 1.0);
		col = mix(col, petal_color.rgb * (0.45 + l * 0.75), petal);
	}
	ALBEDO = col * tint.rgb;
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
}
