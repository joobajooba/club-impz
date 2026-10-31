shader_type sky;
// Biome sky: gradient (sky_top, sky_horizon, ground), drifting pixel-stepped clouds, sun disc, and at
// night (night = 0..1) a deep blue gradient, a moon disc with a soft glow and twinkling stars.
// biome_environment.gd sets every uniform; sun_dir and moon_dir point from the camera to each body.

uniform vec3 sky_top : source_color = vec3(0.35, 0.6, 0.95);
uniform vec3 sky_horizon : source_color = vec3(0.75, 0.88, 1.0);
uniform vec3 ground : source_color = vec3(0.3, 0.35, 0.3);
uniform vec3 sun_color : source_color = vec3(1.0, 0.95, 0.8);
uniform vec3 sun_dir = vec3(0.0, 0.5, 0.86);
uniform vec3 moon_dir = vec3(0.0, 0.5, -0.86);
uniform float night : hint_range(0.0, 1.0) = 0.0;
uniform float cloud_cover = 0.4;

float hash2(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float hash3(vec3 p) {
	p = fract(p * vec3(0.1031, 0.1030, 0.0973));
	p += dot(p, p.yxz + 33.33);
	return fract((p.x + p.y) * p.z);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash2(i), hash2(i + vec2(1.0, 0.0)), f.x), mix(hash2(i + vec2(0.0, 1.0)), hash2(i + vec2(1.0, 1.0)), f.x), f.y);
}

float fbm(vec2 p) {
	return vnoise(p) * 0.65 + vnoise(p * 2.3 + 7.1) * 0.35;  // 2 octaves
}

void sky() {
	vec3 d = normalize(EYEDIR);
	float h = d.y;
	vec3 top = mix(sky_top, vec3(0.02, 0.04, 0.13), night);
	vec3 hor = mix(sky_horizon, vec3(0.07, 0.11, 0.24), night);
	vec3 gnd = mix(ground, ground * 0.18, night);
	vec3 col = h > 0.0 ? mix(hor, top, smoothstep(0.0, 0.55, h)) : mix(hor, gnd, smoothstep(0.0, 0.18, -h));

	float cover = 0.0;
	if (!AT_CUBEMAP_PASS && h > 0.015) {
		// stars: one cell of a direction grid in a few hundred lights up, twinkling
		vec3 cell = floor(d * 160.0);
		float s = hash3(cell);
		float tw = 0.6 + 0.4 * sin(TIME * (2.0 + s * 4.0) + s * 60.0);
		col += vec3(step(0.9965, s) * tw * night * smoothstep(0.02, 0.2, h));
		// clouds on a flat layer above: dir.xz / dir.y, pixel stepped and scrolling
		vec2 uv = d.xz / (h + 0.08) * 1.4 + vec2(TIME * 0.006, TIME * 0.003);
		uv = floor(uv * 48.0) / 48.0;
		float f = fbm(uv * 1.6);
		cover = floor(clamp((f - (1.0 - cloud_cover) * 0.8) * 3.5, 0.0, 1.0) * 3.0) / 3.0;
		cover *= smoothstep(0.015, 0.18, h);
		vec3 cloud_day = mix(vec3(1.0), sky_horizon, 0.25) * (0.85 + 0.15 * f);
		vec3 cloud_night = vec3(0.16, 0.2, 0.3);
		col = mix(col, mix(cloud_day, cloud_night, night), cover * 0.9);
	}
	// sun disc and glow, moon disc and soft glow (behind clouds)
	float sd = dot(d, normalize(sun_dir));
	col += sun_color * (step(0.9993, sd) * 1.5 + pow(max(sd, 0.0), 220.0) * 0.4) * (1.0 - night) * (1.0 - cover);
	float md = dot(d, normalize(moon_dir));
	col += vec3(0.85, 0.9, 1.0) * (step(0.9995, md) * 1.2 + pow(max(md, 0.0), 90.0) * 0.18) * night * (1.0 - cover * 0.8);
	COLOR = col;
}
