# histogram_analysis.py
import matplotlib.pyplot as plt
from PIL import Image

def plot_image_histograms(cover_path, stego_path, output_path=None):
    """Plot RGB histograms for both cover and stego images."""
    try:
        # Load images
        cover_image = Image.open(cover_path).convert('RGB')
        stego_image = Image.open(stego_path).convert('RGB')
        
        # Split channels
        cover_r, cover_g, cover_b = cover_image.split()
        stego_r, stego_g, stego_b = stego_image.split()
        
        # Calculate histograms
        cover_r_hist = cover_r.histogram()
        cover_g_hist = cover_g.histogram()
        cover_b_hist = cover_b.histogram()
        
        stego_r_hist = stego_r.histogram()
        stego_g_hist = stego_g.histogram()
        stego_b_hist = stego_b.histogram()
        
        # Create subplot figure
        fig, axs = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('RGB Channel Histogram Comparison', fontsize=16)
        
        # Plot cover image histograms
        axs[0, 0].bar(range(256), cover_r_hist, color='red', alpha=0.7)
        axs[0, 0].set_title('Cover Image - Red Channel')
        
        axs[0, 1].bar(range(256), cover_g_hist, color='green', alpha=0.7)
        axs[0, 1].set_title('Cover Image - Green Channel')
        
        axs[0, 2].bar(range(256), cover_b_hist, color='blue', alpha=0.7)
        axs[0, 2].set_title('Cover Image - Blue Channel')
        
        # Plot stego image histograms
        axs[1, 0].bar(range(256), stego_r_hist, color='red', alpha=0.7)
        axs[1, 0].set_title('Stego Image - Red Channel')
        
        axs[1, 1].bar(range(256), stego_g_hist, color='green', alpha=0.7)
        axs[1, 1].set_title('Stego Image - Green Channel')
        
        axs[1, 2].bar(range(256), stego_b_hist, color='blue', alpha=0.7)
        axs[1, 2].set_title('Stego Image - Blue Channel')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save or display the plot
        if output_path:
            plt.savefig(output_path)
        else:
            plt.show()
        
        # Calculate and print statistical differences
        print("\nStatistical Analysis:")
        for channel, cover_hist, stego_hist, name in [
            (0, cover_r_hist, stego_r_hist, "Red"),
            (1, cover_g_hist, stego_g_hist, "Green"),
            (2, cover_b_hist, stego_b_hist, "Blue")
        ]:
            diff_sum = sum(abs(c - s) for c, s in zip(cover_hist, stego_hist))
            print(f"{name} channel total difference: {diff_sum}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
