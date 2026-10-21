src = '''U0 KRTest()
{
\tWinMax;
\tGrPrint(gr.dc, 40, 40, "안녕하세요");
\tGrPrint(gr.dc, 40, 60, "TempleOS-Korean 한글 테스트");
\tBusy(120000);
}
Spawn(&KRTest, NULL, "KRTest");
'''
data = src.encode('cp949')
open('/tmp/vdisk/Home/KRTest.ZC', 'wb').write(data)
print('written', len(data))
