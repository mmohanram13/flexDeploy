#!/bin/bash
# Test API endpoints

echo "Testing API endpoints..."
echo ""

echo "1. Dashboard Metrics:"
curl -s http://localhost:8000/api/dashboard/metrics | python3 -m json.tool
echo ""

echo "2. Device Distribution:"
curl -s http://localhost:8000/api/dashboard/device-distribution | python3 -m json.tool
echo ""

echo "3. Devices (first 2):"
curl -s http://localhost:8000/api/devices | python3 -m json.tool | head -50
echo ""

echo "4. Deployments:"
curl -s http://localhost:8000/api/deployments | python3 -m json.tool
echo ""

echo "5. Rings:"
curl -s http://localhost:8000/api/rings | python3 -m json.tool | head -50
