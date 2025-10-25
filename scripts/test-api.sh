#!/bin/bash

# Test DTN Simulator API Endpoints
echo "🧪 Testing DTN Simulator API Endpoints..."
echo ""

BASE_URL="http://localhost:8000"

# Test health endpoint
echo "1. Testing health endpoint..."
HEALTH=$(curl -s "$BASE_URL/api/v2/health")
if echo "$HEALTH" | grep -q '"success":true'; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ Health check failed"
    echo "   Response: $HEALTH"
fi

# Test constellation library
echo ""
echo "2. Testing constellation library..."
CONSTELLATIONS=$(curl -s "$BASE_URL/api/v2/constellation/library")
if echo "$CONSTELLATIONS" | grep -q '"starlink"'; then
    echo "   ✅ Constellation library loaded"
    STARLINK_SATS=$(echo "$CONSTELLATIONS" | grep -o '"satellites":[0-9]*' | head -1 | cut -d: -f2)
    echo "   📡 Starlink constellation: $STARLINK_SATS satellites"
else
    echo "   ❌ Constellation library failed"
fi

# Test simulation endpoints
echo ""
echo "3. Testing simulation creation..."
CREATE_SIM=$(curl -s -X POST "$BASE_URL/api/v2/simulation/create" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test Simulation","constellation_id":"starlink","routing_algorithm":"epidemic","duration":6}')

if echo "$CREATE_SIM" | grep -q '"success":true'; then
    echo "   ✅ Simulation creation works"
    SIM_ID=$(echo "$CREATE_SIM" | grep -o '"simulation_id":"[^"]*"' | cut -d: -f2 | tr -d '"')
    echo "   🆔 Created simulation: $SIM_ID"
else
    echo "   ❌ Simulation creation failed"
fi

# Test simulation list
echo ""
echo "4. Testing simulation list..."
LIST_SIMS=$(curl -s "$BASE_URL/api/v2/simulation/list")
if echo "$LIST_SIMS" | grep -q '"simulations"'; then
    echo "   ✅ Simulation list works"
    SIM_COUNT=$(echo "$LIST_SIMS" | grep -o '"id":"[^"]*"' | wc -l)
    echo "   📊 Found $SIM_COUNT simulations"
else
    echo "   ❌ Simulation list failed"
fi

# Test experiment endpoints
echo ""
echo "5. Testing experiment creation..."
CREATE_EXP=$(curl -s -X POST "$BASE_URL/api/v2/experiment/create" \
    -H "Content-Type: application/json" \
    -d '{"name":"Algorithm Comparison","constellation_id":"starlink","routing_algorithms":["epidemic","prophet"],"duration":24}')

if echo "$CREATE_EXP" | grep -q '"success":true'; then
    echo "   ✅ Experiment creation works"
    EXP_ID=$(echo "$CREATE_EXP" | grep -o '"experiment_id":"[^"]*"' | cut -d: -f2 | tr -d '"')
    echo "   🧪 Created experiment: $EXP_ID"
else
    echo "   ❌ Experiment creation failed"
fi

echo ""
echo "🎯 API Test Summary:"
echo "   Backend API: http://localhost:8000/docs"
echo "   Frontend App: http://localhost:3000"
echo "   Health Status: http://localhost:8000/api/v2/health"
echo ""
echo "✨ DTN Simulator is ready for use!"