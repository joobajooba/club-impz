# Club Impz

Browser game built in Godot, with crypto features, part of the Implingz NFT project. This repository also holds the general website and the Supabase database setup.

## Layout

| Folder | What goes here |
| --- | --- |
| `docs/` | Markdown documents: design docs, specs, plans, notes |
| `godot-game/` | The Godot project (open this folder in Godot) |
| `godot-game/assets/models/` | 3D game models |
| `godot-game/assets/sprites/` | 2D sprites and sprite sheets |
| `godot-game/assets/textures/` | Textures and materials |
| `website/` | The general website |
| `supabase/` | Supabase database: migrations, edge functions, config |
| `tools/` | Helper scripts (for example `generate_terrain_textures.py`) |

Game assets live inside `godot-game/` so Godot can import them (Godot only sees files inside its project folder).
