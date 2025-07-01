import machine
import ili934xnew
import os
import sdcard
# LED Pins
cs_sd = machine.Pin(13, machine.Pin.OUT)
cs_lcd = machine.Pin(17, machine.Pin.OUT)
dc = machine.Pin(16, machine.Pin.OUT)
rst = machine.Pin(21, machine.Pin.OUT)
alert_pin = machine.Pin(22, machine.Pin.OUT)

# LPG LEDs
lpg_led_normal = machine.Pin(6, machine.Pin.OUT)
lpg_led_alert = machine.Pin(3, machine.Pin.OUT)
lpg_led_critical = machine.Pin(0, machine.Pin.OUT)

# CO LEDs
co_led_normal = machine.Pin(7, machine.Pin.OUT)
co_led_alert = machine.Pin(4, machine.Pin.OUT)
co_led_critical = machine.Pin(1, machine.Pin.OUT)

# Methane LEDs
methane_led_normal = machine.Pin(8, machine.Pin.OUT)
methane_led_alert = machine.Pin(5, machine.Pin.OUT)
methane_led_critical = machine.Pin(2, machine.Pin.OUT)

# Sensors pins
mq4 = machine.ADC(machine.Pin(27))
mq6 = machine.ADC(machine.Pin(26))
mq7 = machine.ADC(machine.Pin(28))

# SPI Configuration (Lower Baudrate)
spi = machine.SPI(0, baudrate=10000000, sck=machine.Pin(18), mosi=machine.Pin(19))
spi1 = machine.SPI(1, baudrate=100_000, sck=machine.Pin(10), mosi=machine.Pin(11), miso=machine.Pin(12))

# Initialize Display with Correct Rotation
display = ili934xnew.ILI9341(spi, cs=cs_lcd, dc=dc, rst=rst, w=320, h=240, r=1)