#line 1 "/home/calvin/EC/ESP32Marauder/esp32_marauder/flipperLED.h"
#pragma once

#ifndef flipperLED_h
#define flipperLED_h

#include "configs.h"
#include "settings.h"

#include <Arduino.h>

extern Settings settings_obj;

class flipperLED {

  public:
    void RunSetup();
    void main();
    void attackLED();
    void sniffLED();
    void offLED();
};

#endif
