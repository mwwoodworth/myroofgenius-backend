#!/bin/bash
# Check for common UI/UX issues in the deployed site

echo "🔍 Checking for UI/UX Issues..."
echo "================================"

# Check for viewport issues
echo -e "\n📱 Checking mobile viewport..."
curl -s https://myroofgenius-live-git-main-matts-projects-fe7d7976.vercel.app/ | grep -i "viewport" | head -2

# Check for overlapping fixed elements
echo -e "\n🔧 Checking for fixed/absolute positioning (potential overlaps)..."
curl -s https://myroofgenius-live-git-main-matts-projects-fe7d7976.vercel.app/ | grep -E "fixed|absolute|sticky" | wc -l

# Check for z-index issues
echo -e "\n📊 Checking z-index usage..."
curl -s https://myroofgenius-live-git-main-matts-projects-fe7d7976.vercel.app/ | grep -E "z-[0-9]|z-index" | head -5

# Check for overflow issues
echo -e "\n📜 Checking overflow handling..."
curl -s https://myroofgenius-live-git-main-matts-projects-fe7d7976.vercel.app/ | grep -E "overflow-|scrollbar" | head -5

echo -e "\n✅ UI check complete"