from vpython import *
import random

# --- Simulation Parameters ---
N = 40              # Number of particles
L = 10.0            # Size of the cubic box (from -L/2 to L/2)
r_max = 2.5         # Truncation distance for L-J force
dt = 0.005          # Time step
mass = 1.0          # Particle mass

# --- Visualization Setup ---
scene = canvas(title="Truncated Lennard-Jones Gas", width=800, height=600, center=vec(0,0,0))
# Draw a wireframe box
d = L/2
box_curves = [
    curve(pos=[vec(-d,-d,-d), vec(d,-d,-d), vec(d,d,-d), vec(-d,d,-d), vec(-d,-d,-d)]),
    curve(pos=[vec(-d,-d,d), vec(d,-d,d), vec(d,d,d), vec(-d,d,d), vec(-d,-d,d)]),
    curve(pos=[vec(-d,-d,-d), vec(-d,-d,d)]),
    curve(pos=[vec(d,-d,-d), vec(d,-d,d)]),
    curve(pos=[vec(d,d,-d), vec(d,d,d)]),
    curve(pos=[vec(-d,d,-d), vec(-d,d,d)])
]

# --- Initialize Particles ---
particles = []
for i in range(N):
    # Random positions within the box
    x = (random.random() - 0.5) * (L - 2)
    y = (random.random() - 0.5) * (L - 2)
    z = (random.random() - 0.5) * (L - 2)
    
    # Create the 3D sphere object
    p = sphere(pos=vec(x, y, z), radius=0.4, color=color.cyan)
    
    # Give it a small initial random velocity
    p.v = vec(random.random()-0.5, random.random()-0.5, random.random()-0.5) * 2
    particles.append(p)

# --- Main Simulation Loop (Euler-Cromer Integrator) ---
while True:
    rate(150) # Limit the loop to 150 frames per second for real-time viewing
    
    # 1. Reset forces to zero for this time step
    forces = [vec(0,0,0) for _ in range(N)]
    
    # 2. Calculate pairwise Lennard-Jones forces
    for i in range(N):
        for j in range(i + 1, N):
            r_vec = particles[i].pos - particles[j].pos
            r_mag = mag(r_vec)
            
            # Apply force only if within the truncated cutoff distance
            # (Also prevent divide-by-zero if particles overlap perfectly)
            if 0.1 < r_mag < r_max:
                # Calculate scalar force: F = r^-13 - r^-7
                F_mag = (1.0 / (r_mag**13)) - (1.0 / (r_mag**7))
                
                # Convert to vector force pushing i away from j
                F_vec = F_mag * norm(r_vec)
                
                # Newton's Third Law
                forces[i] += F_vec
                forces[j] -= F_vec

    # 3. Update kinematics and handle wall collisions
    for i in range(N):
        # Euler-Cromer step 1: Update velocity
        particles[i].v += (forces[i] / mass) * dt
        
        # Euler-Cromer step 2: Update position using NEW velocity
        particles[i].pos += particles[i].v * dt
        
        # Simple hard-wall reflective boundaries
        if particles[i].pos.x > L/2:
            particles[i].v.x *= -1
            particles[i].pos.x = L/2
        elif particles[i].pos.x < -L/2:
            particles[i].v.x *= -1
            particles[i].pos.x = -L/2
            
        if particles[i].pos.y > L/2:
            particles[i].v.y *= -1
            particles[i].pos.y = L/2
        elif particles[i].pos.y < -L/2:
            particles[i].v.y *= -1
            particles[i].pos.y = -L/2
            
        if particles[i].pos.z > L/2:
            particles[i].v.z *= -1
            particles[i].pos.z = L/2
        elif particles[i].pos.z < -L/2:
            particles[i].v.z *= -1
            particles[i].pos.z = -L/2
