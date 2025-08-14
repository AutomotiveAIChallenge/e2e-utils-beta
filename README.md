# Automotive AI Challenge e2e_utils_beta

- This repository is intended to be used together with [aichallenge-2025](https://github.com/AutomotiveAIChallenge/aichallenge-2025/tree/main).
- It aims to provide samples and references for those who want to create planners using machine learning (ML).

## e2e_utils_beta Setup Instructions

### 1. Setup environment

- Please follow [this document](https://autowarefoundation.github.io/autoware-documentation/main/installation/autoware/source-installation/#how-to-set-up-a-development-environment) and setup the environment with TensorRT.

```bash
git clone https://github.com/autowarefoundation/autoware.git
cd autoware
```

- After execute the blow command, the command asked the questions. Please answer them.

```bash
./setup-dev-env.sh
```

### 2. Clone the repository

```bash
git clone https://github.com/AutomotiveAIChallenge/e2e-utils-beta
```

### 3. Import dependencies
```bash
sh script/setup.sh
```

### 4. Build
```bash
colcon build --symlink-install --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Release --packages-up-to vad_aic_launch autoware_auto_planning_msgs
```

## Setup AWSIM

- Please use [this branch](https://github.com/AutomotiveAIChallenge/aichallenge-2025-e2e-test) to setup.

- Please follow [this setting up instruction](https://automotiveaichallenge.github.io/aichallenge-documentation-2025/setup/requirements.html).

## Run Sample ROS Node(VLM-Planner)

### Environment Setup

- Please install `uv` by following [this document](https://docs.astral.sh/uv/getting-started/installation/).

```sh
cd e2e-utils-beta;source install/setup.bash
```

```sh
cd src/vlm_planner;uv venv -p python3.10
```

```sh
source .venv/bin/activate
```

```sh
uv pip install .
```

### Set Gemini API Key

- Please get your Gemini API Key in Google AI Studio following [this instruction](https://ai.google.dev/gemini-api/docs/api-key?hl=ja).

```sh
export GEMINI_API_KEY="YOUR_API_KEY"
```

### Run AWSIM

- Please run AWSIM following [this instruction](https://automotiveaichallenge.github.io/aichallenge-documentation-2025/setup/visible-simulation.html)

```sh
(AIC_DEV) user_name:/aichallenge$ ./run_evaluation.bash 
```

### Run 

```sh
# Run the VLM planner node with custom output topic
cd e2e-utils-beta/src/vlm_planner
python vlm_planner_node.py --ros-args -p output_topic:="/planning/ml_planner/auto/trajectory"
```

### Tips

- You can change model by updating [the code](./src/vlm_trajectory_selector/vlm_planner.py)
    - In default, `gemini-2.5-flash-lite` is used.

```python
self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
```

- You can update [the prompt](./src/vlm_trajectory_selector/prompt.py).

- [Fine Tuning on vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-use-supervised-tuning?hl=ja) may be helpful to improve the trajectory.

## Run Sample ROS Node(VAD)

- Use 3 terminals

### Run AWSIM(terminal 1)

- Please run AWSIM following [this instruction](https://automotiveaichallenge.github.io/aichallenge-documentation-2025/setup/visible-simulation.html)

```sh
(AIC_DEV) user_name:/aichallenge$ ./run_evaluation.bash 
```

### Run VAD and dummy publisher (terminal 2)

```sh
cd e2e-utils-beta;source install/setup.bash
```

```sh
ros2 launch vad_aic_launch vad_aic.launch.xml use_sim_time:=true
```

### Run VLM trajectory selector(terminal 3)

#### Environment Setup

```sh
cd e2e-utils-beta;source install/setup.bash
```

```sh
cd src/vlm_trajectory_selector;uv venv -p python3.10
```

```sh
source .venv/bin/activate
```

```sh
uv pip install .
```

#### Set Gemini API Key

- Please get your Gemini API Key in Google AI Studio following [this instruction](https://ai.google.dev/gemini-api/docs/api-key?hl=ja).

```sh
export GEMINI_API_KEY="YOUR_API_KEY"
```

#### Run trajectory selector

```sh
cd src/vlm_trajectory_selector
python trajectory_selector.py --ros-args -p input_topic:="/planning/vad/trajectories_base" -p output_topic:="/planning/ml_planner/auto/trajectory"
```
