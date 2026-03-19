
This is a remix of the [Qt Py Snap Fit Case](https://learn.adafruit.com/qt-py-snap-fit-case/overview)
for [FeatherWing Doubler](https://www.adafruit.com/product/2890) with RFM69 module with external RP-SMA antenna mounted with
the [edge connector](https://www.adafruit.com/product/1865).

The Doubler mount and the battery holder are taken from the
[Color Sensing Music Player](https://learn.adafruit.com/color-sensing-music-player)
so this is in fact a remix and mashup.

This is meant for both sender (with 2000mAh battery) as well as the
[receiver](https://github.com/vladak/radio2mqtt) (without battery).

## Print parameters

The printing should be done using similar parameters as the QtPy case:
  - PLA filament 220C extruder
  - 0.2 layer height
  - grid pattern infill 15% density
  - no ironing
  - Arachne generator
  - 60mm/s print speed
  - 60C heated bed
  - perimeter/wall thickness 2
  - first/last layer thickness: 5 and 4, respectively
  - use supports + brim (for the middle part of the case)

In my case the parameter set was called "0.2 STRUCTURAL".

Took me some 5 iterations of prints to get the dimensions/tolerances/printing right.

Printed on Prusa MK4S, slicing done in PrusaSlicer.

## Assembly/mount

1. Use M2.5 x 6mm screws to attach the Doubler to the bottom of the case.
2. If battery is used, snap fit the battery using the holder.
3. Insert any cables (USB and/or STEMMA QT) through the USB hole.
4. Attach any sensors using nylon screws to the top lid.
5. Close the top lid.
6. Attach to a surface using screws with 3 mm diameter.

## Lessons learned

### Tolerances

At first I tried to have some space between the battery clip and the rails on the bottom of the case, concretely 1mm, thinking 0.5 mm on each side would be fine. Turned out the clip was actually loose. Making the inner length to match the distance between rails exactly did the trick.

### Distortions

When printing on MK4S, some of the corners of the middle of the case were a bit (like 1 mm) lifted as if distorted/bent by an upward force. So there was a tiny gap between the bottom lid and the middle part of the case. This happened twice on MK4S. When printing with supports in the USB and antenna holes the case seems to be straight. I also tried printing on Prusa Core One (without supports) and there was an interesting effect of the side of the case next to the antenna hole actually moving during printing. It might be interesting to try the print with supports and also a brim to prevent the print from moving. I belive the upward bent was caused by the case moving even in the case (sic!) of MK4S where the base plate moves rather than in the case of Prusa Core One where only the head moves in the x/y axes. Another idea that might be worth experimenting with is the position of the seam (try it in the middle perhaps rather than in the corner). Or try increasing wall thickness (which is parametrized).

So, supports seem to be handly also for fixing the print horizontally, not only vertically.
