Visu pirma, jei anbo neveikia reikia ji pabandyt du kartus restartint tiesiog istraukus ir idejus rozete.




Tada, jei vis tiek neveikia:
ssh is kompo (ka reikia zinot yra "general dalykai.txt")



sshinus i raspberry pi tada reikia pradet nuo logu


1. bandyt "journalctl -u anbo -n 1000"

sitas ismes paskutini 1000 eiluciu output (galima ir maziau jei reikia) 

"G" paspaudus nuves i pacia apacia logu


Tada is error linu ziuret kas blogai buvo ir kada suluzo (laikas yra UTC regis)

2. Jei neaisku dar tada galima pabandyt scripta runnint 

"sudo systemctl stop anbo"

"source env/bin/activate"
"cd anbo_main"
"cd code"
"sudo pigpiod"
"python3 main.py"



3. Tada jei kazkas konkreciai neveikia galima naudotis helper scriptais:
buttonTest.py - konkretu mygtuka patikrint (galima keist scripte yra eilute cfg.MAG_PIN ir pan)
distSensorTest.py - jei neveikia ultrasoundas po kojom kur yra //todo
derivative_adc_monitor.py - tikrint pumpavimo funkcija (servo nejudina)
testProp.py - propeleri pajungia (kartu ir jo skaitliukus)

