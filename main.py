import yt_dlp
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

def extract_video_info(video_url):
    ydl_opts = {
        'skip_download': True,  # don't download the video
        'writeinfojson': True,
        'quiet': True,          # don't print progress
        'no_warnings': True   
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        if info is None:
            raise ValueError(f"Error while extracting info for {video_url}")
        return info

def validate_key(key, info, video_url, required=False):
    if key not in info or info[key] is None:
        if required:
            raise ValueError(f"No {key} data found for {video_url}")
        else:
            print(f"No {key} data found for {video_url}")
            return None
    return info[key]

def visualize_heatmap(info, output_file, show_chapters):
    heatmap_data  = validate_key('heatmap', info, url, required=True)

    sns.set_style("whitegrid")
    sns.set_context("notebook", font_scale=1.2)
    
    end_times = [point['end_time'] for point in heatmap_data]
    
    x_points = []
    y_points = []
    
    for i, point in enumerate(heatmap_data):
        x_points.append(point['start_time'])
        y_points.append(point['value'])
        
        if i < len(heatmap_data) - 1:
            x_points.append(point['end_time'])
            y_points.append(point['value'])
    
    if heatmap_data:
        x_points.append(heatmap_data[-1]['end_time'])
        y_points.append(heatmap_data[-1]['value'])
    
    fig, ax = plt.subplots(figsize=(16, 7))
    
    colors = [(0.1, 0.1, 0.5), (0.2, 0.2, 0.8), (0.8, 0.2, 0.2), (0.5, 0, 0)]  # blue to red gradient
    cm = LinearSegmentedColormap.from_list('most_replayed_cmap', colors, N=100)
    
    for i in range(len(x_points)-1):
        ax.fill_between([x_points[i], x_points[i+1]], 
                        [0, 0], 
                        [y_points[i], y_points[i+1]], 
                        color=cm(y_points[i]),
                        alpha=0.85)
    
    ax.plot(x_points, y_points, 'k-', alpha=0.7, linewidth=1.5)
    
    max_time = max(end_times) if end_times else 0
    ax.set_xlim(0, max_time)
    ax.set_ylim(0, 1.05)
    
    ax.set_xlabel('Time (seconds)', fontsize=12, labelpad=10)
    ax.set_ylabel('Most Replayed', fontsize=12, labelpad=10)
    ax.set_title('YouTube Most Replayed Heatmap', fontsize=16, pad=20, weight='bold')
    
    if max_time > 60:
        from matplotlib.ticker import FuncFormatter
        def format_time(x, pos):
            minutes = int(x // 60)
            seconds = int(x % 60)
            return f'{minutes:02d}:{seconds:02d}'
        
        ax.xaxis.set_major_formatter(FuncFormatter(format_time))
    
    sm = plt.cm.ScalarMappable(cmap=cm, norm=plt.Normalize(vmin=0, vmax=1))
    cbar = plt.colorbar(sm, ax=ax, pad=0.02)
    # cbar.set_label('Most Replayed', fontsize=10)
    cbar.ax.tick_params(labelsize=9)
    
    ax.grid(True, linestyle='--', alpha=0.3)
    
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('white')
    
    ax.grid(which='minor', linestyle=':', alpha=0.2)
    ax.minorticks_on()
    
    chapters_data = validate_key('chapters', info, url)
    if show_chapters and chapters_data:
        for chapter in chapters_data:
            # add vertical line for chapter start
            ax.axvline(x=chapter['start_time'], color='gray', linestyle='--', alpha=0.5)
            
            # add chapter title
            ax.text(chapter['start_time'], -0.15, chapter['title'],
                   rotation=45, ha='left', va='top',
                   fontsize=5, color='gray')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    
    plt.show()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--video_id", type=str, required=True, help="YouTube video ID")
    parser.add_argument("--save_info", type=bool, default=True, help="Save info")
    parser.add_argument("--show_chapters", type=bool, default=False, help="Show chapters if available")
    args = parser.parse_args()

    video_id = args.video_id

    os.makedirs('./output/heatmaps', exist_ok=True)
    os.makedirs('./output/info', exist_ok=True)

    url = f"https://www.youtube.com/watch?v={video_id}"
    info = extract_video_info(url)

    if args.save_info:
        with open(f'./output/info/{video_id}.json', 'w') as f:
            json.dump(info, f, indent=4)

    visualize_heatmap(info, output_file=f"./output/heatmaps/{video_id}.png", show_chapters=args.show_chapters)
    
