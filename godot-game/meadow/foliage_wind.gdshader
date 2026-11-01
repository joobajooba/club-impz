shader_type spatial;
// Stylized foliage: wind sway, soft "up" normals so grass blends with the ground,
// darker roots and large-scale colour variation across the meadow.
render_mode cull_disabled, depth_draw_opaque, diffuse_lambert, specular_disabled;

uniform sampler2D albedo_tex : source_color, hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec4 albedo_col : source_color = vec4(1.0);
uniform bool use_scissor = false;
uniform float scissor_threshold = 0.5;
uniform float height_ref = 1.5;        // model-space height, used for sway / root darkening
uniform float wind_strength = 0.1;     // metres of sway at the tip
uniform float wind_speed = 1.4;
uniform float normal_up = 1.0;         // 1 = fully ground-aligned lighting
uniform float base_darken = 0.45;
uniform vec3 tint_a : source_color = vec3(1.0);
uniform vec3 tint_b : source_color = vec3(1.0);

varying float v_h;
varying float v_tint;

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_h = clamp(VERTEX.y / max(height_ref, 0.001), 0.0, 1.0);
	float t = TIME * wind_speed;
	float gust = sin(t + wp.x * 0.35 + wp.z * 0.2) * 0.6
			+ sin(t * 2.7 + wp.x * 1.7 - wp.z * 1.3) * 0.25 + 0.35;
	vec3 offs = vec3(gust, 0.0, gust * 0.45) * wind_strength * v_h * v_h;
	VERTEX += inverse(mat3(MODEL_MATRIX)) * offs;
	float n = sin(wp.x * 0.13 + 1.7) * sin(wp.z * 0.11 - 0.4) + 0.5 * sin((wp.x - wp.z) * 0.27);
	v_tint = clamp(n * 0.5 + 0.5, 0.0, 1.0);
}

void fragment() {
	vec4 tex = texture(albedo_tex, UV) * albedo_col;
	if (use_scissor && tex.a < scissor_threshold) {
		discard;
	}
	vec3 col = tex.rgb * mix(tint_a, tint_b, v_tint);
	col *= mix(1.0 - base_darken, 1.0, v_h);
	ALBEDO = col;
	ROUGHNESS = 1.0;
	vec3 up_view = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
	NORMAL = normalize(mix(NORMAL, up_view, normal_up));
}
