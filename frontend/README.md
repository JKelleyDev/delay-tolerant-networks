# GUI – 3D Earth Visualization

This is the starting point for **Pair 3 (GUI & Visualization)** in the Delay Tolerant Networks project.  
It uses **React + Vite** with **Three.js, React-Three-Fiber, and Drei** to render a 3D Earth.

## What’s Included
- React + Vite scaffold for fast development
- A textured Earth that spins slowly
- Mouse controls (drag to rotate, scroll to zoom) via Drei’s OrbitControls
- Clean setup to add satellites, arcs, and visualization features

## Prerequisites
- [Node.js](https://nodejs.org) v22.x or newer  
- npm v10.x or newer (comes with Node.js)

⚠️ **Note:** If you just installed Node.js, you may need to **close and reopen your terminal** before running the commands below so that `node` and `npm` are recognized.

## Getting Started
# Navigate to SRC folder
cd src

# Install backend dependencies
pip install -r requirements.txt

# Run the API
python orbital_mechanics.py api

# Navigate to GUI folder
cd ..
cd gui

# Install dependencies
npm install

# Start the dev server
npm run dev

# Click the http:// link  to open the globe in browser

# Controls
Press 1: Earth centered 
Left drag: Rotate
Right drag: Pan
Scroll: Zoom
Press 2: Follow Satellite
Press 3: Ground Mode
Press 4: Free flight
*** These features are clunky, press ESC to get your cursor back ***
