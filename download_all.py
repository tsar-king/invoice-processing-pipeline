# download_all.py
from datasets import load_dataset
from tqdm import tqdm
import os

dataset = load_dataset('katanaml-org/invoices-donut-data-v1', split='train')
os.makedirs('input_invoices_all', exist_ok=True)

for i in tqdm(range(len(dataset)), desc="Downloading all invoices"):
    dataset[i]['image'].save(f'input_invoices_all/invoice_{i:04d}.jpg')

print(f'✅ Downloaded {len(dataset)} invoices')