import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const srcDir = path.resolve(__dirname, 'dist');
const destDir = path.resolve(__dirname, '../backend/static');

try {
  // Clear destDir if it exists
  if (fs.existsSync(destDir)) {
    fs.rmSync(destDir, { recursive: true, force: true });
    console.log(`Cleared existing backend static directory: ${destDir}`);
  }
  
  // Create destDir
  fs.mkdirSync(destDir, { recursive: true });
  
  // Copy recursively
  fs.cpSync(srcDir, destDir, { recursive: true, force: true });
  console.log(`Successfully synced build: ${srcDir} -> ${destDir}`);
} catch (err) {
  console.warn('Warning: Could not copy frontend build to backend static folder (this is expected if deploying frontend separately):', err.message);
}
