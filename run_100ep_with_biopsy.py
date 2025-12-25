"""
Run 100 Episodes với Brain Biopsy
==================================
Chạy experiment với SNN và analyze learning progress mỗi 25 episodes.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import json
import os
import sys
import argparse
from datetime import datetime

# Add project root to path
sys.path.append('.')

from src.tools.brain_biopsy_theus import BrainBiopsyTheus


def run_with_biopsy():
    """Run 100 episodes với brain biopsy checkpoints."""
    parser = argparse.ArgumentParser(description="100 Episodes với Brain Biopsy")
    parser.add_argument('--config', type=str, default='experiments_sensor_100ep.json',
                        help='Experiment config file')
    parser.add_argument('--biopsy-interval', type=int, default=25,
                        help='Biopsy mỗi N episodes')
    parser.add_argument('--output-dir', type=str, default='results/biopsy',
                        help='Output directory')
    args = parser.parse_args()
    
    # Load config
    with open(args.config) as f:
        config = json.load(f)
    
    print("=" * 70)
    print("RUN 100 EPISODES WITH BRAIN BIOPSY")
    print("=" * 70)
    print(f"Config: {args.config}")
    print(f"Biopsy interval: {args.biopsy_interval} episodes")
    print(f"Output: {args.output_dir}")
    print()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # NOTE: Sử dụng main.py logic để chạy experiment
    # Nhưng thêm biopsy checkpoints
    
    print("⚠️  IMPLEMENTATION NOTE:")
    print("Script này cần integrate với main.py để chạy thực tế.")
    print("Hiện tại chỉ là template outline.")
    print()
    print("CẦN:")
    print("1. Import và sử dụng main() từ main.py")
    print("2. Hook vào episode loop để chạy biopsy")
    print("3. Save biopsy reports mỗi checkpoint")
    print()
    
    # Pseudo-code cho implementation thực tế:
    # 
    # from main import main as run_experiment
    # 
    # # Modify main() để accept callback
    # def biopsy_callback(episode, engines):
    #     if episode % args.biopsy_interval == 0:
    #         print(f"\n{'='*60}")
    #         print(f"BRAIN BIOPSY - Episode {episode}")
    #         print(f"{'='*60}")
    #         
    #         # Analyze agent 0
    #         snn_ctx = engines[0].ctx.domain_ctx.snn_context
    #         
    #         # Population stats
    #         pop_info = BrainBiopsyTheus.inspect_population(snn_ctx)
    #         print(json.dumps(pop_info, indent=2))
    #         
    #         # Causality learning
    #         causality = BrainBiopsyTheus.inspect_causality(snn_ctx)
    #         print(json.dumps(causality, indent=2))
    #         
    #         # Save report
    #         report = {
    #             'episode': episode,
    #             'timestamp': datetime.now().isoformat(),
    #             'population': pop_info,
    #             'causality': causality,
    #         }
    #         
    #         filename = f"{args.output_dir}/biopsy_ep{episode}.json"
    #         BrainBiopsyTheus.export_to_json(report, filename)
    # 
    # # Run experiment với callback
    # run_experiment(
    #     num_episodes=100,
    #     episode_callback=biopsy_callback
    # )
    
    print("=" * 70)
    print("Để chạy thực tế, cần modify main.py để support callbacks.")
    print("=" * 70)


if __name__ == '__main__':
    run_with_biopsy()
