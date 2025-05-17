Anbo pagrindinis networkas:

SSID:ButasDulkese2
PW:StatybvieteNo1

*reikia hotspota susikurt per telefona su situ networku, nes netraukia pagrindinis muziejaus. (Arba galima jau prisijungus prie jo pridet dar belenkoki su nmcli)

tada jei prijungtas i ta pati networka, 

ssh anbo@anbo
password: anbo lektuvelis


*jei ka tai galima neprisijungus prie to paties networko per Lenovo pilka laptopa dirbtuviu. (Jis turi tailscale, tai kad galima butu sshint tiesiog reikia "Tailscale" ijungt)


Pagrindinis service kuris runnina visa anbo yra /etc/systemd/system/anbo.service






VEIKIMO PRINCIPAS:
-----------------------------------------------------

yra 3 bendrai (micro)processoriai:
Raspberry Pi 4 - atsakingas uz garsa ir uz visa gameloopa
Pico - atsakingas uz ADC inputus (voztuvas ir gazas) ir taip pat atsakingas uz arduino ijungima
Arduino Uno - atsakingas uz propelerio veikima

Schema kaip viskas veikia ir kokie pinai ir protokolai jungimo yra KiCad failuose.
-----------------------------------------------------
also kode viskas suvardinta angliskai nes ne debilas esu




