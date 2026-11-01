// Recolours a textured kit model (a plant, flower or tree) to one tier colour.
// Keeps the texture's light and dark detail and its cut-out alpha, swaps its hue for `tint`.
shader_type spatial;
render_mode cull_disabled, depth_prepass_alpha;

uniform sampler2D tex : source_color, filter_linear_mipmap;
uniform vec4 tint : source_color = vec4(1.0);
uniform float alpha_cut = 0.5;
uniform float roughness_value = 0.85;
uniform float glow = 0.0;

void fragment() {
	vec4 c = texture(tex, UV);
	float l = dot(c.rgb, vec3(0.299, 0.587, 0.114));
	ALBEDO = tint.rgb * (0.55 + l * 0.9);
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = alpha_cut;
	ROUGHNESS = roughness_value;
	EMISSION = tint.rgb * glow;
}
