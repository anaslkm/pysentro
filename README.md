# pysentro

repo contains 2 main functions in sdk:

- code for decoding sentronic NIR instruments telegrams using the sentronic SDK tcp/ip protocol -> sentro_telegram.py
- code for creating commands to the instruments based on SDK tcp/ip protocol -> sentro_command.py

Some use case examples are contained in tests dir

possible type of commands:
- StartMeasurement
- StopMeasurement
- SingleMeasSample
