import flet as ft
import math 

# --- 1. カスタムボタンクラス ---
class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text
        self.style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(30)),
        )
        self.height = 70

class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        CalcButton.__init__(self, text, button_clicked, expand)
        self.bgcolor = ft.Colors.WHITE24
        self.color = ft.Colors.WHITE

class ActionButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1): # ActionButtonもexpandを受け取るように修正
        CalcButton.__init__(self, text, button_clicked, expand)
        self.bgcolor = ft.Colors.ORANGE
        self.color = ft.Colors.WHITE

class ExtraActionButton(CalcButton):
    # 🚨 修正点: expand 引数を受け取るように変更
    def __init__(self, text, button_clicked, expand=1):
        # CalcButton.__init__ に expand を渡す
        CalcButton.__init__(self, text, button_clicked, expand) 
        self.bgcolor = ft.Colors.BLUE_GREY_100
        self.color = ft.Colors.BLACK

# --- 2. メインアプリクラス (変更なし) ---
class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.reset()

        self.result = ft.Text(value="0", color=ft.Colors.WHITE, size=48, weight=ft.FontWeight.W_200) 
        self.width = 350
        self.bgcolor = ft.Colors.BLACK
        self.border_radius = ft.border_radius.all(20)
        self.padding = 20
        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.result], alignment=ft.MainAxisAlignment.END), 
                ft.Divider(height=1, color=ft.Colors.WHITE24),
                
                # Row 1 (AC, sqrt, +/-, ^)
                ft.Row(
                    controls=[
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),
                        ExtraActionButton(text="sqrt", button_clicked=self.button_clicked), 
                        ExtraActionButton(text="+/-", button_clicked=self.button_clicked),
                        ActionButton(text="^", button_clicked=self.button_clicked), 
                    ]
                ),
                # Row 2 (sin, cos, tan, log, pi, e) - 6ボタン
                ft.Row(
                    controls=[
                        # expand=1 が正しく渡されるようになりました
                        ExtraActionButton(text="sin", button_clicked=self.button_clicked, expand=1), 
                        ExtraActionButton(text="cos", button_clicked=self.button_clicked, expand=1), 
                        ExtraActionButton(text="tan", button_clicked=self.button_clicked, expand=1), 
                        ExtraActionButton(text="log", button_clicked=self.button_clicked, expand=1), 
                        ExtraActionButton(text="π", button_clicked=self.button_clicked, expand=1), 
                        ExtraActionButton(text="e", button_clicked=self.button_clicked, expand=1), 
                    ]
                ),
                # Row 3 (7, 8, 9, /)
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="/", button_clicked=self.button_clicked), 
                    ]
                ),
                # Row 4 (4, 5, 6, *)
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ActionButton(text="*", button_clicked=self.button_clicked),
                    ]
                ),
                # Row 5 (1, 2, 3, -)
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="-", button_clicked=self.button_clicked),
                    ]
                ),
                # Row 6 (0, ., +, =)
                ft.Row(
                    controls=[
                        DigitButton(text="0", expand=2, button_clicked=self.button_clicked),
                        DigitButton(text=".", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),
                        ActionButton(text="=", button_clicked=self.button_clicked),
                    ]
                ),
            ],
            spacing=10
        )

    # ロジックメソッド (button_clicked, format_number, calculate) は変更なし
    def reset(self):
        self.operator = "+"
        self.operand1 = 0.0
        self.new_operand = True
        self.pending_op = False 

    def button_clicked(self, e):
        data = e.control.data
        
        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"
            self.reset()
            self.update()
            return
            
        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if "e" in str(self.result.value).lower() and not self.new_operand:
                 self.result.value = "0" 
                 self.new_operand = True
            
            if data == "." and "." in str(self.result.value):
                return

            if self.result.value == "0" or self.new_operand:
                if data == "." and self.result.value == "0":
                    self.result.value = "0."
                elif data == ".":
                    self.result.value = "0."
                else:
                    self.result.value = data
                self.new_operand = False
            else:
                self.result.value += data

        elif data in ("π", "e"):
            if data == "π":
                value = math.pi
            else: 
                value = math.e
                
            self.result.value = str(self.format_number(value))
            self.new_operand = True
            
        elif data in ("+", "-", "*", "/", "^"):
            try:
                current_value = float(self.result.value)
            except ValueError:
                self.result.value = "Error"
                self.reset()
                self.update()
                return

            if self.pending_op:
                self.operand1 = self.calculate(self.operand1, current_value, self.operator)
                self.result.value = str(self.format_number(self.operand1))
            else:
                self.operand1 = current_value
                self.pending_op = True 

            self.operator = data
            self.new_operand = True 
        
        elif data == "=":
            if self.pending_op:
                try:
                    operand2 = float(self.result.value)
                except ValueError:
                    self.result.value = "Error"
                    self.reset()
                    self.update()
                    return
                    
                self.operand1 = self.calculate(self.operand1, operand2, self.operator)
                
                if self.operand1 == "Error":
                    self.result.value = "Error"
                else:
                    self.result.value = str(self.format_number(self.operand1))
                
                self.pending_op = False 
                self.new_operand = True 
        
        elif data in ("%", "+/-", "sqrt", "sin", "cos", "tan", "log"):
            try:
                current_value = float(self.result.value)
                result = current_value

                if data == "%":
                    result = current_value / 100

                elif data == "+/-":
                    result = -current_value
                
                elif data == "sqrt":
                    if current_value < 0:
                        self.result.value = "Error"
                        self.reset()
                        self.update()
                        return
                    result = math.sqrt(current_value)
                
                elif data == "log":
                    if current_value <= 0:
                        self.result.value = "Error"
                        self.reset()
                        self.update()
                        return
                    result = math.log10(current_value)

                elif data == "sin":
                    result = math.sin(math.radians(current_value))
                
                elif data == "cos":
                    result = math.cos(math.radians(current_value))

                elif data == "tan":
                    angle_deg = current_value % 180
                    if abs(angle_deg - 90) < 1e-9 or abs(angle_deg + 90) < 1e-9: 
                        self.result.value = "Error" 
                        self.reset()
                        self.update()
                        return
                    result = math.tan(math.radians(current_value))

                self.result.value = str(self.format_number(result))
                self.new_operand = True 
            
            except Exception:
                self.result.value = "Error"
        
        self.update()

    def format_number(self, num):
        if num == "Error":
            return "Error"
            
        if not isinstance(num, (int, float)) or math.isinf(num) or math.isnan(num):
             return "Error"

        abs_num = abs(num)
        
        if (abs_num >= 10**10) or (0 < abs_num < 10**-6):
            return f"{num:.8e}"
        
        if num == int(num):
            if abs(int(num)) >= 10**10:
                 return f"{num:.8e}"
            return int(num)
        
        else:
            num_str = f"{num:.10f}"
            return float(num_str.rstrip('0').rstrip('.'))

    def calculate(self, operand1, operand2, operator):
        try:
            if operator == "+":
                return operand1 + operand2
            elif operator == "-":
                return operand1 - operand2
            elif operator == "*":
                return operand1 * operand2
            elif operator == "/":
                if operand2 == 0:
                    return "Error"
                else:
                    return operand1 / operand2
            elif operator == "^": 
                return math.pow(operand1, operand2)
        except Exception:
            return "Error"


# --- 3. アプリケーションのエントリーポイント ---
def main(page: ft.Page):
    page.title = "Scientific Calculator"
    page.theme_mode = ft.ThemeMode.DARK
    
    calc = CalculatorApp()
    page.add(calc)


ft.app(target=main)

