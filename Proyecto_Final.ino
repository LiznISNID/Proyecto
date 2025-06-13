#include <Keypad.h>
#include <LiquidCrystal.h>
#include <Servo.h>

LiquidCrystal lcd(A0, A1, A2, A3, A4, A5);
Servo motor;
const byte FILAS = 4;
const byte COLUMNAS = 4;

char teclas[FILAS][COLUMNAS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

byte pinesFilas[FILAS] = {13, 12, 11, 10};
byte pinesColumnas[COLUMNAS] = {9, 8, 7, 6};

Keypad teclado = Keypad(makeKeymap(teclas), pinesFilas, pinesColumnas, FILAS, COLUMNAS);

String clave = "123456";   
String ingreso = "";       
int intentos = 0;          
int LED1 = 4; 
int LED2 = 3;
int rostro;

void bloqueo() {
  for (int i = 30; i >= 0; i--) {
    digitalWrite(LED1, HIGH);
    delay(250);
    digitalWrite(LED1, LOW);
    delay(100);  
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(" BLOQUEO ");
    lcd.print(i);
    lcd.print(" seg");
    delay(600);
  }
  intentos = 0;
  digitalWrite(LED1, LOW);
}

void desbloqueo(){
  digitalWrite(LED2, HIGH);
  motor.write(90);
  delay(5000);
  motor.write(0);
  digitalWrite(LED2, LOW);
}

void setup() {
  Serial.begin(9600); 
  motor.attach(5);
  motor.write(0);
  lcd.begin(16, 2);
  lcd.clear();
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  digitalWrite(LED1, LOW);
  digitalWrite(LED2, LOW);
}

void loop() {
  lcd.setCursor(0, 0);
  lcd.print(" INGRESA CODIGO ");
  lcd.setCursor(5, 1);
  lcd.print(ingreso);
  if (Serial.available() > 0) {
    rostro = Serial.read();
    if (rostro == 'C') {
      lcd.clear();
      lcd.setCursor(5, 0);
      lcd.print("ROSTRO");
      lcd.setCursor(3, 1);
      lcd.print("RECONOCIDO");
      delay(1500);
      intentos = 0;
      desbloqueo();
    } 
    else if (rostro == 'D'){
      lcd.clear();
      lcd.setCursor(5, 0);
      lcd.print("ROSTRO");
      lcd.setCursor(1, 1);
      lcd.print("NO AUTORIZADO");
      digitalWrite(LED1, HIGH);
      delay(2000);
      digitalWrite(LED1, LOW); 
    }
    lcd.clear();
  }
  char tecla = teclado.getKey();
  if (tecla) {
    if (tecla == '*') {
      ingreso = "";
      lcd.setCursor(0, 1);
      lcd.print("                ");
    } 
    else if (ingreso.length() < 6) {
      ingreso += tecla;
    }
    if (ingreso.length() == 6) {
      lcd.setCursor(5, 1);
      lcd.print(ingreso);
      delay(500);
      lcd.clear();
      if (ingreso == clave) {
        lcd.setCursor(0, 0);
        lcd.print("ACCESO PERMITIDO");
        delay(3000);
        intentos = 0;  
        desbloqueo();
      } else {
        lcd.setCursor(0, 0);
        lcd.print(" ACCESO DENEGADO");
        digitalWrite(LED1, HIGH);
        delay(2000);
        digitalWrite(LED1, LOW); 
        intentos++;
        if (intentos >= 3) {
          bloqueo();
        }
      }
      ingreso = "";
      lcd.clear();
    }
  }
}