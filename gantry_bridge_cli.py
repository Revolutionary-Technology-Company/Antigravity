#!/usr/bin/env python3
"""
Revolutionary Technology - Avionics & Signal Bridge
Integrates Hexadecimal Digital Signals with the Type-S Central Hub.
Exports Gantry 5 YAML configurations and automates 3D/Video media generation.
"""

import typer
import yaml
import subprocess
from pathlib import Path
import pyttsx3 

app = typer.Typer(
    name="GantryBridge", 
    help="Hexadecimal Signal to Type-S Computer Bridge",
    add_completion=False
)

REPO_ROOT = Path(__file__).parent

@app.command()
def build_gantry_config(
    particle_name: str = typer.Option("hex_quantum_hub", help="Name of the Gantry 5 particle"),
    buffer_size: str = typer.Option("800QGb", help="Data buffer size for the signal router")
):
    """
    Generates a Gantry 5 YAML configuration file for web deployment.
    Drop this into your Gantry 'custom/particles' directory to enable the 3D Viewer.
    """
    # Gantry 5 standard Particle YAML structure
    config = {
        "name": particle_name,
        "description": "3D Hexadecimal Signal Computer Viewer",
        "type": "particle",
        "icon": "fa-microchip",
        "configuration": {
            "caching": {"type": "static"},
            "fields": {
                "signal_mode": {
                    "type": "select",
                    "default": "hexadecimal",
                    "options": {"hexadecimal": "Hex Signal", "binary": "Binary Pulse"}
                },
                "buffer_capacity": {
                    "type": "input.text",
                    "default": buffer_size,
                    "label": "Double Latch Gate Buffer Capacity"
                },
                "render_engine": {
                    "type": "select",
                    "default": "webgl",
                    "label": "Viewer Engine"
                }
            }
        }
    }
    
    out_path = REPO_ROOT / f"{particle_name}.yaml"
    with open(out_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
    typer.secho(f"Gantry 5 particle configuration saved to {out_path}", fg=typer.colors.GREEN)

@app.command()
def render_computer(
    component: str = typer.Argument("central_hub_saiya_v4", help="SCAD file to render"),
    camera_angle: str = typer.Option("75,0,45", help="OpenSCAD camera angle")
):
    """
    Renders the completed computer hub into 3D models (STL) and Pictures (PNG).
    """
    scad_file = REPO_ROOT / f"{component}.scad"
    if not scad_file.exists():
        typer.secho(f"CRITICAL: {scad_file.name} not found in the root directory.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    stl_out = REPO_ROOT / f"{component}_model.stl"
    png_out = REPO_ROOT / f"{component}_render.png"
    
    typer.echo(f"Compiling 3D Model ({stl_out.name})...")
    subprocess.run(["openscad", "-o", str(stl_out), str(scad_file)])
    
    typer.echo(f"Capturing Hardware Image ({png_out.name})...")
    subprocess.run(["openscad", "-o", str(png_out), "--camera", f"0,0,0,{camera_angle},500", str(scad_file)])
    
    typer.secho("Rendering complete. STL and PNG assets verified.", fg=typer.colors.CYAN)

@app.command()
def generate_media(
    component: str = typer.Argument("central_hub_saiya_v4"),
    duration: int = typer.Option(6, help="Video duration in seconds")
):
    """
    Generates dynamic CLI Audio and mixes it with the 3D renders to create a showcase video.
    """
    audio_file = REPO_ROOT / "hex_signal_telemetry.wav"
    png_out = REPO_ROOT / f"{component}_render.png"
    video_out = REPO_ROOT / f"{component}_showcase.mp4"
    
    if not png_out.exists():
        typer.secho(f"Rendered image not found. Run 'render-computer {component}' first.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo("Synthesizing Typer Audio Briefing...")
    engine = pyttsx3.init()
    # You can adjust the voice properties (rate, volume) here if needed
    engine.setProperty('rate', 160) 
    
    # The script generated for the video audio
    script = "Initializing Hexadecimal Signal processing across the cross-coupled inverters. Quantum memory buffer sequence nominal."
    engine.save_to_file(script, str(audio_file))
    engine.runAndWait()
    
    typer.echo("Encoding Video with FFmpeg...")
    
    # FFmpeg command to loop the rendered image and mix it with the generated audio track
    ffmpeg_cmd = [
        "ffmpeg", "-y", 
        "-loop", "1", "-i", str(png_out),
        "-i", str(audio_file), 
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k", 
        "-pix_fmt", "yuv420p",
        "-shortest", "-t", str(duration), 
        str(video_out)
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
