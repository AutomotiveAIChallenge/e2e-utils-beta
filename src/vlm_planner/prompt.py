# prompt.py

initial_position = (89633.29, 43127.57, 0.8778)
breaking_point_in_first_sector = (89616.0, 43156.0, 0.0)
entry_point_in_second_sector = (89613.9, 43157.7, 0.0)
apex_point_in_second_sector = (89617.0, 43166.0, 0.0)
end_point_in_second_sector = (89620.0, 43164.0, 0.0)

def calculate_distance(point1: tuple, point2: tuple) -> float:
    """Calculate the Euclidean distance between two points."""
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

def create_trajectory_prompt(last_trajectory_action: str, last_sector: int, current_velocity: float, current_position: tuple, last_commands: list[str]) -> str:
    track_knowledge = f"""Track sectors:
    1: 32m Starting Straight (speed limit 5 m/s). At the end of the straight in sector 1, there is the white big sign board. Before you pass 28m, you can go straight. After you pass 28m, the blue and white stripe wall became closer, and please slow down with big braking for sector 2 while keeping the steering straight. DON'T turn right before you passed breaking point; distance from braking point {calculate_distance(current_position, breaking_point_in_first_sector)} m
    2: R-Hairpin. distance from current position to sector 2 entry {calculate_distance(current_position, entry_point_in_second_sector)} m. distance from current position to sector 2 apex {calculate_distance(current_position, apex_point_in_second_sector)} m. distance from current position to sector 2 end {calculate_distance(current_position, end_point_in_second_sector)} m.
    3: 30m Short Straight
    4: L-Hairpin
    5: 30m Short Straight
    6: U-shaped Right
    7: 90-degree Left
    8: R-Hairpin
    9: L-Hairpin
    10: S-Curve (L->R)
    11: 90-degree Right
    12: S-Curve (L->R)
    13: Sweeping Right Corner (leads to main straight)"""

    # command logs (maximum 20 commands)
    last_commands_str = ', '.join(last_commands[-20:]) if last_commands else 'None'

    prompt = f"""
    Assume I am at the coordinate (0,0) facing forward along the x-axis.
    Based on the given image of a race track, choose the best trajectory to drive the car.
    The road is the dark gray area. Stay on the road. The wall has a blue and white pattern.
    
    Command options (output one of these for the next action):
    - turn right
    - turn left
    - go straight

    History:
    - Last Trajectory: {last_trajectory_action}
    - Last sector: {last_sector}
    - Current Velocity: {current_velocity:.2f} m/s
    - Current Position: distance from initial position: {calculate_distance(current_position, initial_position):.2f} m
    - Last 20 commands: {last_commands_str}
    {track_knowledge}
    Your task: Determine the current sector and generate a trajectory and command.
    What is my future trajectory in next 5 seconds under vehicle coordinate?

    Generate 10 trajectory points with:
    - x, y, z coordinates (vehicle coordinate system, x: forward, y: left, z: up)
    - time: time from now (0.0 to 5.0 seconds)
    - velocity: target velocity in m/s

    Ensure smooth trajectory that follows the road and maintains safe driving.
    Don't forget that the sector 2 is a right hairpin. Before that, you should slow down.
    Don't forget that if you want to turn right, y shoud be negative.
    What is my future trajectory in next 5 seconds under vehicle coordinate?
    Output format:
    {{
      "current_sector": int,
      "command": "turn right|turn left|go straight",
      "trajectory_points": [
        {{"x": float, "y": float, "z": float, "time": float, "velocity": float}},
        ... (10 points)
      ],
      "reasoning": "string explaining your decision"
    }}
    """
    return prompt
