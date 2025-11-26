from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet
import re

class ValidatePrediccionForm(FormValidationAction):
    """Validación personalizada del formulario de predicción"""

    def name(self) -> Text:
        return "validate_prediccion_form"

    # Diccionarios de mapeo (texto a número)
    DIAS_SEMANA = {
        "domingo": 0, "dom": 0,
        "lunes": 1, "lun": 1,
        "martes": 2, "mar": 2,
        "miércoles": 3, "miercoles": 3, "mie": 3,
        "jueves": 4, "jue": 4,
        "viernes": 5, "vie": 5,
        "sábado": 6, "sabado": 6, "sab": 6
    }

    CONTROL_CRUCE = {
        "sin control": 0, "ninguno": 0, "nada": 0, "sin": 0,
        "stop": 1, "señal de stop": 1, "señales de stop": 1, "alto": 1,
        "semáforo": 2, "semaforo": 2, "luz": 2, "luces": 2,
        "rotonda": 3, "glorieta": 3, "redondel": 3,
        "semáforo con sensor": 4, "semaforo con sensor": 4, "sensor": 4,
        "señales de prioridad": 5, "prioridad": 5, "señal de prioridad": 5,
        "otro": 6, "otra": 6, "otro control": 6
    }

    TIPO_CRUCE = {
        "cruce simple": 0, "simple": 0, "normal": 0,
        "cruce en t": 1, "t": 1, "cruce t": 1,
        "cruce en y": 2, "y": 2, "cruce y": 2,
        "cruce múltiple": 3, "cruce multiple": 3, "múltiple": 3, "multiple": 3,
        "rotonda": 4, "glorieta": 4, "redondel": 4,
        "entrada": 5, "salida": 5, "entrada/salida privada": 5, "privada": 5,
        "otro": 6, "otra": 6
    }

    LUZ = {
        "día": 0, "dia": 0, "luz del día": 0, "plena luz": 0, "de día": 0, "claro": 0,
        "oscuro sin iluminación": 1, "oscuro sin luz": 1, "sin luz": 1, "muy oscuro": 1,
        "oscuro con iluminación": 1, "oscuro con luz": 2, "con luz": 2, "alumbrado": 2,
        "amanecer": 3, "atardecer": 3, "anochecer": 3, "penumbra": 3,
        "niebla": 4, "humo": 4, "neblina": 4,
        "otro": 5, "otra": 5
    }

    SUPERFICIE = {
        "seco": 0, "asfalto seco": 0, "seca": 0, "dry": 0,
        "húmedo": 1, "humedo": 1, "mojado": 1, "asfalto húmedo": 1, "mojada": 1, "wet": 1,
        "hielo": 2, "nieve": 2, "helado": 2, "congelado": 2,
        "grava": 3, "gravilla": 3, "piedritas": 3,
        "otro": 4, "otra": 4
    }

    TIPO_VIA = {
        "calle": 0, "callejón": 0, "callejon": 0,
        "avenida": 1, "av": 1, "ave": 1,
        "carretera principal": 2, "autopista": 2, "principal": 2,
        "carretera secundaria": 3, "secundaria": 3, "vía secundaria": 3,
        "rotonda": 4, "glorieta": 4, "redondel": 4,
        "otro": 5, "otra": 5
    }

    CLIMA = {
        "despejado": 0, "soleado": 0, "sol": 0, "claro": 0, "buen tiempo": 0,
        "lluvia ligera": 1, "llovizna": 1, "lluvia leve": 1, "chispeando": 1,
        "lluvia intensa": 2, "lluvia fuerte": 2, "tormenta": 2, "aguacero": 2, "diluvio": 2,
        "niebla": 3, "neblina": 3, "bruma": 3,
        "nieve": 4, "nevada": 4, "nevando": 4,
        "viento fuerte": 5, "ventoso": 5, "viento": 5, "vendaval": 5,
        "otro": 6, "otra": 6
    }

    VEHICULO = {
        "coche": 0, "carro": 0, "auto": 0, "automóvil": 0, "automovil": 0, "sedan": 0,
        "motocicleta": 1, "moto": 1, "motorbike": 1, "motorcycle": 1,
        "camión": 2, "camion": 2, "truck": 2, "trailer": 2,
        "autobús": 3, "autobus": 3, "bus": 3, "buseta": 3,
        "bicicleta": 4, "bici": 4, "bike": 4, "cicla": 4,
        "peatón": 5, "peaton": 5, "persona": 5, "caminando": 5, "a pie": 5,
        "otro": 6, "otra": 6
    }

    AREA = {
        "urbano": 0, "urbana": 0, "ciudad": 0, "urbano": 0,
        "rural": 1, "campo": 1, "zona rural": 1
    }

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Text]:
        """Lista de slots requeridos"""
        return [
            "day_of_week",
            "junction_control",
            "junction_detail",
            "light_conditions",
            "local_authority",
            "road_surface",
            "road_type",
            "speed_limit",
            "urban_rural",
            "weather",
            "vehicle_type",
            "casualties",
            "num_vehicles"
        ]

    def validate_day_of_week(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar día de la semana"""
        texto = str(slot_value).lower().strip()
        
        # Intentar convertir de texto a número
        if texto in self.DIAS_SEMANA:
            valor = self.DIAS_SEMANA[texto]
            print(f"✅ DEBUG - Día convertido: '{texto}' -> {valor}")
            return {"day_of_week": valor}
        
        # Si ya es un número, validarlo
        try:
            valor = int(float(texto))
            if 0 <= valor <= 6:
                print(f"✅ DEBUG - Día válido: {valor}")
                return {"day_of_week": valor}
        except:
            pass
        
        dispatcher.utter_message(text="❌ No entendí el día. Por favor escribe el nombre del día (ej: lunes, martes) o el número (0-6).")
        return {"day_of_week": None}

    def validate_junction_control(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar control de cruce"""
        texto = str(slot_value).lower().strip()
        
        if texto in self.CONTROL_CRUCE:
            valor = self.CONTROL_CRUCE[texto]
            print(f"✅ DEBUG - Control de cruce: '{texto}' -> {valor}")
            return {"junction_control": valor}
        
        try:
            valor = int(float(texto))
            if 0 <= valor <= 6:
                return {"junction_control": valor}
        except:
            pass
        
        dispatcher.utter_message(text="❌ No entendí el tipo de control. Ejemplos: 'semáforo', 'stop', 'rotonda', 'sin control'")
        return {"junction_control": None}

    def validate_junction_detail(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar detalle de cruce"""
        texto = str(slot_value).lower().strip()
        
        if texto in self.TIPO_CRUCE:
            valor = self.TIPO_CRUCE[texto]
            print(f"✅ DEBUG - Tipo de cruce: '{texto}' -> {valor}")
            return {"junction_detail": valor}
        
        try:
            valor = int(float(texto))
            if 0 <= valor <= 6:
                return {"junction_detail": valor}
        except:
            pass
        
        dispatcher.utter_message(text="❌ No entendí el tipo de cruce. Ejemplos: 'cruce en T', 'rotonda', 'cruce simple'")
        return {"junction_detail": None}

    def validate_light_conditions(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar condiciones de luz"""
        texto = str(slot_value).lower().strip()
        
        if texto in self.LUZ:
            valor = self.LUZ[texto]
            print(f"✅ DEBUG - Luz: '{texto}' -> {valor}")
            return {"light_conditions": valor}
        
        try:
            valor = int(float(texto))
            if 0 <= valor <= 5:
                return {"light_conditions": valor}
        except:
            pass
        
        dispatcher.utter_message(text="❌ No entendí las condiciones de luz. Ejemplos: 'día', 'oscuro', 'amanecer', 'niebla'")
        return {"light_conditions": None}

    def validate_local_authority(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar distrito"""
        texto = str(slot_value).strip()
        
        distritos_validos = [0, 1, 3, 4, 76, 159, 176, 267, 384]
        
        try:
            valor = int(float(texto))
            if valor in distritos_validos:
                print(f"✅ DEBUG - Distrito: {valor}")
                return {"local_authority": valor}
        except:
            pass
        
        dispatcher.utter_message(text=f"❌ Distrito no válido. Distritos disponibles: {', '.join(map(str, distritos_validos))}")
        return {"local_authority": None}

    def validate_road_surface(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar superficie de la vía"""
        texto = str(slot_value).lower().strip()
        
        if texto in self.SUPERFICIE:
            valor = self.SUPERFICIE[texto]
            print(f"✅ DEBUG - Superficie: '{texto}' -> {valor}")
            return {"road_surface": valor}
        
        try:
            valor = int(float(texto))
            if 0 <= valor <= 4:
                return {"road_surface": valor}
        except:
            pass
        
        dispatcher.utter_message(text="❌ No entendí la condición de la vía. Ejemplos: 'seco', 'húmedo', 'hielo', 'grava'")
        return {"road_surface": None}

    def validate_road_type(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar tipo de vía"""
        texto = str(slot_value).lower().strip()
        
        if texto in self.TIPO_VIA:
            valor = self.TIPO_VIA[texto]
            print(f"✅ DEBUG - Tipo de vía: '{texto}' -> {valor}")
            return {"road_type": valor}
        
        try:
            valor = int(float(texto))
            if 0 <= valor <= 5:
                return {"road_type": valor}
        except:
            pass
        
        dispatcher.utter_message(text="❌ No entendí el tipo de vía. Ejemplos: 'calle', 'avenida', 'autopista', 'carretera'")
        return {"road_type": None}

    def validate_speed_limit(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar límite de velocidad"""
        texto = str(slot_value).strip()
        
        try:
            valor = int(float(texto))
            if valor >= 0:
                print(f"✅ DEBUG - Velocidad: {valor}")
                return {"speed_limit": valor}
        except:
            pass
        
        dispatcher.utter_message(text="❌ No entendí el límite de velocidad. Ejemplos: '30', '40', '50', '60', '70', '80', '90', '100', '110', '120', '150', '200'")
        return {"speed_limit": None}

    def validate_urban_rural(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar área urbana/rural"""
        texto = str(slot_value).lower().strip()
        
        if texto in self.AREA:
            valor = self.AREA[texto]
            print(f"✅ DEBUG - Área: '{texto}' -> {valor}")
            return {"urban_rural": valor}
        
        try:
            valor = int(float(texto))
            if valor in [0, 1]:
                return {"urban_rural": valor}
        except:
            pass
        
        dispatcher.utter_message(text="❌ No entendí. Escribe 'urbano' o 'rural'")
        return {"urban_rural": None}

    def validate_weather(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar clima"""
        texto = str(slot_value).lower().strip()
        
        if texto in self.CLIMA:
            valor = self.CLIMA[texto]
            print(f"✅ DEBUG - Clima: '{texto}' -> {valor}")
            return {"weather": valor}
        
        try:
            valor = int(float(texto))
            if 0 <= valor <= 6:
                return {"weather": valor}
        except:
            pass
        
        dispatcher.utter_message(text="❌ No entendí el clima. Ejemplos: 'despejado', 'lluvia', 'niebla', 'nieve'")
        return {"weather": None}

    def validate_vehicle_type(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar tipo de vehículo"""
        texto = str(slot_value).lower().strip()
        
        if texto in self.VEHICULO:
            valor = self.VEHICULO[texto]
            print(f"✅ DEBUG - Vehículo: '{texto}' -> {valor}")
            return {"vehicle_type": valor}
        
        try:
            valor = int(float(texto))
            if 0 <= valor <= 6:
                return {"vehicle_type": valor}
        except:
            pass
        
        dispatcher.utter_message(text="❌ No entendí el tipo de vehículo. Ejemplos: 'coche', 'moto', 'camión', 'bus', 'bicicleta'")
        return {"vehicle_type": None}

    def validate_casualties(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar número de víctimas"""
        texto = str(slot_value).lower().strip()
        
        # Mapeo de texto a número
        numeros_texto = {
            "ninguna": 0, "cero": 0, "sin víctimas": 0, "ninguno": 0, "0": 0,
            "una": 1, "uno": 1, "1": 1,
            "dos": 2, "2": 2,
            "tres": 3, "3": 3,
            "cuatro": 4, "4": 4,
            "cinco": 5, "más de cinco": 5, "5": 5, "muchas": 5
        }
        
        if texto in numeros_texto:
            valor = numeros_texto[texto]
            print(f"✅ DEBUG - Víctimas: '{texto}' -> {valor}")
            return {"casualties": valor}
        
        try:
            valor = int(float(texto))
            if valor >= 5:
                valor = 5
            if 0 <= valor <= 5:
                return {"casualties": valor}
        except:
            pass
        
        dispatcher.utter_message(text="❌ No entendí. Escribe el número de víctimas (0-5) o 'ninguna', 'una', 'dos', etc.")
        return {"casualties": None}

    def validate_num_vehicles(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar número de vehículos"""
        texto = str(slot_value).lower().strip()
        
        # Mapeo de texto a número
        numeros_texto = {
            "uno": 1, "un": 1, "1": 1,
            "dos": 2, "2": 2,
            "tres": 3, "3": 3,
            "cuatro": 4, "4": 4,
            "cinco": 5, "más de cinco": 5, "5": 5, "muchos": 5
        }
        
        if texto in numeros_texto:
            valor = numeros_texto[texto]
            print(f"✅ DEBUG - Vehículos: '{texto}' -> {valor}")
            return {"num_vehicles": valor}
        
        try:
            valor = int(float(texto))
            if valor >= 5:
                valor = 5
            if 1 <= valor <= 5:
                return {"num_vehicles": valor}
        except:
            pass
        
        dispatcher.utter_message(text="❌ No entendí. Escribe el número de vehículos (1-5) o 'uno', 'dos', 'tres', etc.")
        return {"num_vehicles": None}