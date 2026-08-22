# AGENTS.md

Guidance for AI coding agents working on RockingMan-PiCar.

RockingMan-PiCar is a personal robotics development layer for an Adeept PiCar-Pro V2.0 running on a Raspberry Pi 5. This repository contains custom RockingMan code, experiments, documentation, and workflow tools. The official Adeept software is an external vendor dependency and is expected outside this repository at `~/Adeept_PiCar-Pro`.

## Core Principles

- Preserve existing working functionality.
- Inspect the existing architecture before proposing rewrites.
- Prefer small, testable, reversible changes.
- Clearly label VERIFIED facts versus INFERENCES when inspecting or summarizing the project.
- Do not treat experiments as production architecture without evidence.
- Do not execute repository code, tests, scripts, services, or hardware-facing commands unless explicitly authorized by the user.

## Repository Boundaries

Distinguish these areas clearly:

- Official Adeept/vendor code: external dependency at `~/Adeept_PiCar-Pro`; do not modify it unless explicitly requested.
- Custom RockingMan-PiCar code: this repository.
- ROS 2 work: keep separate from existing non-ROS scripts unless the user explicitly asks to integrate them.
- AI/LLM features: keep separate from hardware-control paths unless explicitly designed and safety-reviewed.
- Experiments: preserve as experiments unless promoted deliberately.

Do not casually merge these boundaries. If a change crosses boundaries, explain why and what risks it introduces.

## Current Architecture Map

Known repository areas:

- `car/`: core hardware profile, actuator abstraction, sensor abstraction, unified robot facade, smoke tests, calibration scripts.
- `car/hardware_profile.py`: verified hardware constants and calibration values. Treat this as a project truth source where applicable.
- `car/robot_hardware.py`: safe actuator wrapper over Adeept `Move`, `RPIservo`, and `Switch`.
- `car/robot_sensors.py`: sensor abstraction for battery ADC, ultrasonic, line sensors, MPU6050, and camera.
- `car/robot.py`: unified facade combining hardware and sensors.
- `autonomy/`: autonomous behavior. Current obstacle guard imports the unified `Robot` facade.
- `arm/`: arm calibration and motion experiments.
- `display/`: OLED status and display experiments.
- `rc/`: remote-control experiments, including joystick and UDP control.
- `shows/`: choreographed demo/show scripts, currently using direct hardware control.
- `system/`: shutdown and emote scripts, including service and poweroff behavior.
- `docs/`: project documentation, including hardware baseline.
- `logs/`: engineering session logs.
- `tools/`: JARVIS workflow/logging shell helpers.

Prefer the shared `car/` abstractions for new reusable robot behavior. Do not rewrite standalone experiments into the shared architecture unless explicitly requested.

## Hardware Safety Rules

Never casually change motor, servo, GPIO, PWM, I2C, SPI, power, wiring, sensor, camera, battery, or hardware calibration behavior.

Never assume from repository contents that the robot is currently powered, connected, stationary, lifted off the ground, mechanically clear, or safe to move.

Before proposing or implementing hardware-control changes:

- Identify which hardware could move or be affected.
- Explain the physical risk, including collision, servo strain, over-travel, battery, wiring, poweroff, or sensor misread risks.
- Prefer stationary verification before movement tests.
- Prefer low-speed, low-angle, short-duration tests before broader movement.
- Preserve failsafe behavior such as motor stop, neutral pose, watchdog stop, cleanup handlers, and resource close/deinit logic.
- Do not execute hardware-facing scripts unless the user explicitly authorizes that exact action.

Before any physical movement or actuator test, require explicit user authorization and confirmation of relevant physical safety conditions.

Examples of hardware-facing code include, but are not limited to:

- Adeept `Move`, `RPIservo`, `Switch`, `Ultra`, `RobotLight`
- `gpiozero`
- `smbus`
- `busio`
- `PCA9685`
- `adafruit_motor`
- `cv2.VideoCapture`
- OLED display libraries
- `systemctl poweroff`
- scripts in `car/`, `arm/`, `rc/`, `shows/`, `display/`, and `system/`

## Calibration and Truth Sources

Treat these files carefully:

- `car/hardware_profile.py`
- `docs/HARDWARE_BASELINE.md`
- `arm/arm_config.py`
- `car/chassis_config.py`
- calibration and baseline scripts under `car/` and `arm/`

`car/hardware_profile.py` and `docs/HARDWARE_BASELINE.md` contain physically verified project information. Older experiments, comments, vendor defaults, or inferred values must not silently override verified project values.

If two sources conflict, stop and report the conflict rather than guessing. Do not automatically modify either truth source merely to make them agree.

Do not change calibration constants unless the user explicitly requests calibration work or provides verified new measurements. When calibration changes are made, identify related documentation that should be updated.

## Development Workflow

Before changing code:

- Read the relevant files.
- Understand existing behavior and dependency boundaries.
- Check whether the requested change belongs in core code, an experiment, docs, or a new isolated module.
- Prefer minimal edits that preserve existing public behavior.
- Avoid broad refactors unless the user explicitly asks for one.

When implementing:

- Keep changes small and reversible.
- Avoid introducing new dependencies unless clearly justified.
- Keep safety checks and cleanup paths intact.
- Do not remove working scripts just because they are experimental.
- Do not import or execute repository modules as a way to inspect them if doing so may touch hardware.

## Verification

After implementation, define verification steps.

Use this order when possible:

1. Static inspection.
2. Safe non-hardware checks, such as formatting, syntax, or lint checks that do not import or execute hardware modules.
3. Non-hardware unit tests, if present and safe.
4. Hardware-facing tests only with explicit user authorization.
5. Stationary hardware verification before movement.
6. Low-risk movement verification before higher-risk behavior.

If verification cannot be performed safely, say so and provide the exact manual verification plan instead.

## Documentation

After a verified meaningful change, identify documentation that should be updated.

Likely documentation targets:

- `README.md`
- `docs/HARDWARE_BASELINE.md`
- `docs/GIT_WORKFLOW.md`
- relevant engineering logs under `logs/`

Do not update logs, docs, or generated artifacts unless the user asks for that change or it is part of the requested implementation.

## Git Rules

Read-only Git inspection commands may be used when appropriate, such as checking the current branch, status, log, or diff.

Do not create, delete, rename, switch, merge, rebase, reset, clean, commit, push, pull, tag, or otherwise change Git or repository state without explicit user instruction.

Never use destructive Git operations such as reset, clean, checkout, or force-push unless the user explicitly requests that exact operation and the risk is clear.

Prefer branches for experiments and keep Git history clean when the user authorizes Git state changes.

## Reporting Expectations

When inspecting the project, separate:

- VERIFIED: facts directly observed in repository files.
- INFERENCE: reasonable conclusions that still need confirmation.
- UNKNOWN: things that cannot be determined from static inspection.

When proposing changes, include:

- affected files
- expected behavior change
- hardware risk level
- verification plan
- documentation follow-up
