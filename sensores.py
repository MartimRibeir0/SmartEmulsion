import time
import random
import threading
from database import save_reading

class SensorManager:
    def __init__(self):
        self.running = False
        self.current_data = {
            "ph": 7.0,
            "oil": 5.0,
            "level": 20.0,  # Litros atuais (simulado)
            "level_percent": 20.0,
            "tank_name": "Tanque Principal",
            "capacity": 500.0,
            "valve_open": False,
            "pump_running": False
        }
        
        # Configurações da Bomba Peristáltica (Óleo)
        # 1140 ml/min = 1.14 L/min
        self.OIL_PUMP_RATE_L_MIN = 1.14 
        
        # Lock para evitar conflitos de threads
        self.lock = threading.Lock()

    def read_sensors(self):
        """Lê os sensores. No futuro, aqui entrará a leitura do ADS1115 e GPIO."""
        with self.lock:
            # Simulamos flutuação ligeira se não estivermos a encher
            if not self.current_data["valve_open"] and not self.current_data["pump_running"]:
                self.current_data["ph"] = round(random.uniform(6.4, 6.6), 2)
                self.current_data["oil"] = round(random.uniform(5.3, 5.5), 2)
            
            # Atualizar percentagem baseada na capacidade
            self.current_data["level_percent"] = round((self.current_data["level"] / self.current_data["capacity"]) * 100, 1)
            
        return self.current_data

    def start_monitoring(self, interval=5):
        self.running = True
        def loop():
            print("Iniciando monitorização de hardware...")
            while self.running:
                data = self.read_sensors()
                save_reading(data["tank_name"], data["ph"], data["oil"], data["level_percent"])
                time.sleep(interval)
        
        thread = threading.Thread(target=loop, daemon=True)
        thread.start()

    def process_fill(self, target_level_liters, oil_to_add_liters):
        """Lógica de controlo dos atuadores."""
        
        # 1. Lógica da Bomba de Óleo (Por Tempo)
        if oil_to_add_liters > 0:
            def run_pump():
                with self.lock: self.current_data["pump_running"] = True
                
                # Tempo = Litros / Taxa
                minutes = oil_to_add_liters / self.OIL_PUMP_RATE_L_MIN
                seconds = minutes * 60
                
                print(f"[BOMBA] Adicionando {oil_to_add_liters}L de óleo. Tempo estimado: {seconds:.1f}s")
                
                # Simulação de enchimento gradual no software
                steps = 20
                for _ in range(steps):
                    time.sleep(seconds / steps)
                    with self.lock:
                        self.current_data["level"] += oil_to_add_liters / steps
                
                with self.lock: self.current_data["pump_running"] = False
                print("[BOMBA] Óleo adicionado com sucesso.")

            threading.Thread(target=run_pump).start()

        # 2. Lógica da Eletroválvula de Água (Por Sensor de Pressão/Nível)
        def run_valve():
            with self.lock: 
                if self.current_data["level"] >= target_level_liters:
                    print("[VALVULA] Nível já atingido ou superior.")
                    return
                self.current_data["valve_open"] = True
            
            print(f"[VALVULA] Aberta. Enchendo até {target_level_liters}L...")
            
            # Simula a água a entrar (no futuro, isto é apenas o tempo que a válvula fica aberta)
            while True:
                time.sleep(0.5) # Frequência de verificação do sensor de pressão
                with self.lock:
                    # Simula subida de 1 litro por segundo (exemplo)
                    self.current_data["level"] += 0.5 
                    
                    if self.current_data["level"] >= target_level_liters:
                        self.current_data["level"] = target_level_liters
                        self.current_data["valve_open"] = False
                        print("[VALVULA] Nível alvo atingido. Válvula fechada.")
                        break
        
        threading.Thread(target=run_valve).start()

# Instância global
sensor_manager = SensorManager()
