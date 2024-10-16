from controller import STmic

# controller = STmic()
# print(controller.read_voltage_avg())
# del controller

controller = STmic()
controller.start_operation()
del controller