We're able to read *something* from the LiveOV7670 ino project. But it's weird.

We can read the first frame, and that seems like it might be OK. It's all blue. But after that we're
unable to read more bytes from the serial port. It's like the port gets stuck, or that the sending end
won't send more. I can't see why.

But if I restart pygrab, then it starts reading bytes again. There's something about reading from the 
existing Serial object (or process) that causes problems. I don't know.

I think the best way forward to is to figure out why we can't read more than one frame from a pygrab
process. It's probably something dumb. After that, we can see what frames we're getting. Then we
can think about converting it from an ino project to a simpler C++ project.

Projects/Links
=====

ov7670-no-ram-arduino-uno
-------------------------

This seems like a very promising reader:

https://github.com/ComputerNerd/ov7670-no-ram-arduino-uno

LiveOV7670
----------

This ino project also might be helpful.

https://github.com/indrekluuk/LiveOV7670