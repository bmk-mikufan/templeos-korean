// TempleOS-Korean V5.03 -- build the distribution ISO.
// Same as Misc/DoDistro.HC, but the source trees are recompressed before the
// ISO is packed so the image stays near the original ~17 MB instead of ~50 MB.
// /0000Boot must stay uncompressed -- the boot loader reads it raw.

U0 MakeKRISO(U8 *fn)
{
  U8 *o=FileNameAbs(fn);

  DelTree("/Distro");
  Del(o);
  DirMk("/Distro");
  In("TB\nScale2Mem(2048,0x40000)\nT \n\n\n\n");
  BootDVDIns;

  Copy("/*","/Distro");
  Del("/Distro/Kernel.BIN.C");
  CopyTree("/0000Boot",  "/Distro/0000Boot");
  CopyTree("/Home",      "/Distro/Home");
  CopyTree("/Adam",      "/Distro/Adam");
  CopyTree("/Apps",      "/Distro/Apps");
  CopyTree("/Compiler",  "/Distro/Compiler");
  CopyTree("/Demo",      "/Distro/Demo");
  CopyTree("/Doc",       "/Distro/Doc");
  CopyTree("/Kernel",    "/Distro/Kernel");
  CopyTree("/Misc",      "/Distro/Misc");
  DirMk("/Distro/Tmp");
  DirMk("/Distro/Tmp/ScrnShots");

  "Compressing trees...\n";
  Zip("::/Distro/Adam/*","+r");
  Zip("::/Distro/Apps/*","+r");
  Zip("::/Distro/Compiler/*","+r");
  Zip("::/Distro/Demo/*","+r");
  Zip("::/Distro/Doc/*","+r");
  Zip("::/Distro/Home/*","+r");
  Zip("::/Distro/Kernel/*","+r");
  Zip("::/Distro/Misc/*","+r");

  "Packing ISO...\n";
  RedSeaISO(o,"/Distro","/Distro/0000Boot/0000Kernel.BIN.C");
  "ISO done: %s\n",o;
  Free(o);
}

MakeKRISO("/Tmp/MyDistro.ISO.C");
