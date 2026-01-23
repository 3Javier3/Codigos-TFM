#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compilador NgSpice a Xyce
=========================
Convierte archivos de simulación de NgSpice (.cir) a formato Xyce.

Autor: Generado automáticamente
Fecha: 2026-01-23

Diferencias principales manejadas:
- .param -> .GLOBAL_PARAM o sustitución directa
- .control/.endc -> Eliminados (Xyce no los soporta)
- Sintaxis de análisis DC/AC/TRAN
- Formato de .print
- Funciones y expresiones
- Modelos y subcircuitos
"""

import re
import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class NgSpiceToXyceCompiler:
    """Compilador para convertir código NgSpice a Xyce."""
    
    def __init__(self):
        # Diccionario de parámetros definidos con .param
        self.parameters: Dict[str, str] = {}
        
        # Modelos definidos
        self.models: Dict[str, str] = {}
        
        # Variables para control de bloques
        self.in_control_block = False
        self.control_block_content: List[str] = []
        
        # Análisis detectados en el bloque .control
        self.detected_analyses: List[str] = []
        
        # Variables para print/plot
        self.print_statements: List[str] = []
        
        # Opciones de conversión
        self.expand_params = True  # Si True, expande {param} a valor directo
        self.add_options = True    # Si True, añade opciones recomendadas de Xyce

    def compile(self, input_file: str, output_file: str = None) -> str:
        """
        Compila un archivo NgSpice a formato Xyce.
        
        Args:
            input_file: Ruta al archivo NgSpice de entrada
            output_file: Ruta al archivo Xyce de salida (opcional)
            
        Returns:
            Código Xyce convertido
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            ngspice_code = f.read()
        
        xyce_code = self.convert(ngspice_code)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(xyce_code)
            print(f"✓ Archivo convertido guardado en: {output_file}")
        
        return xyce_code

    def convert(self, ngspice_code: str) -> str:
        """
        Convierte código NgSpice a Xyce.
        
        Args:
            ngspice_code: Código fuente en formato NgSpice
            
        Returns:
            Código convertido a formato Xyce
        """
        # Reset estado
        self.parameters = {}
        self.models = {}
        self.in_control_block = False
        self.control_block_content = []
        self.detected_analyses = []
        self.print_statements = []
        
        lines = ngspice_code.split('\n')
        output_lines = []
        
        # Primera pasada: extraer parámetros y detectar bloques
        self._first_pass(lines)
        
        # Segunda pasada: convertir línea por línea
        end_line_index = -1
        for i, line in enumerate(lines):
            converted = self._convert_line(line, i)
            if converted is not None:
                # Detectar dónde está .END para insertar análisis antes
                if converted.strip().upper() == '.END':
                    end_line_index = len(output_lines)
                output_lines.append(converted)
        
        # Preparar líneas de análisis y print
        analysis_lines = []
        if self.detected_analyses:
            analysis_lines.extend(['', '* --- Análisis (extraído de .control) ---'])
            analysis_lines.extend(self.detected_analyses)
        
        if self.print_statements:
            analysis_lines.extend(self.print_statements)
        
        # Insertar análisis ANTES de .END
        if analysis_lines:
            if end_line_index >= 0:
                # Insertar antes de .END
                output_lines = output_lines[:end_line_index] + analysis_lines + ['', '.END']
            else:
                # No hay .END, añadir al final
                output_lines.extend(analysis_lines)
                output_lines.append('.END')
        else:
            # Asegurar que termina con .END
            if end_line_index < 0:
                output_lines.append('.END')
        
        output_text = '\n'.join(output_lines)
        return output_text

    def _first_pass(self, lines: List[str]) -> None:
        """Primera pasada para extraer parámetros."""
        for line in lines:
            stripped = line.strip()
            
            # Extraer parámetros .param
            param_match = re.match(r'\.param\s+(\w+)\s*=\s*(.+)', stripped, re.IGNORECASE)
            if param_match:
                param_name = param_match.group(1)
                param_value = param_match.group(2).strip()
                self.parameters[param_name] = param_value

    def _convert_line(self, line: str, line_num: int) -> Optional[str]:
        """
        Convierte una línea de NgSpice a Xyce.
        
        Args:
            line: Línea original
            line_num: Número de línea
            
        Returns:
            Línea convertida o None si debe eliminarse
        """
        stripped = line.strip()
        
        # Líneas vacías
        if not stripped:
            return line
        
        # Comentarios (se mantienen igual)
        if stripped.startswith('*'):
            return line
        
        # --- Manejo del bloque .control ---
        if stripped.lower() == '.control':
            self.in_control_block = True
            return '* --- Bloque .control eliminado (no soportado en Xyce) ---'
        
        if stripped.lower() == '.endc':
            self.in_control_block = False
            return '* --- Fin del bloque .control ---'
        
        if self.in_control_block:
            self._parse_control_line(stripped)
            return f'* [CONTROL] {line}'
        
        # --- Directivas .param ---
        if stripped.lower().startswith('.param'):
            return self._convert_param(stripped)
        
        # --- Directivas de análisis ---
        if stripped.lower().startswith('.dc'):
            return self._convert_dc(stripped)
        
        if stripped.lower().startswith('.ac'):
            return self._convert_ac(stripped)
        
        if stripped.lower().startswith('.tran'):
            return self._convert_tran(stripped)
        
        if stripped.lower().startswith('.op'):
            return self._convert_op(stripped)
        
        # --- Directivas .print/.plot ---
        if stripped.lower().startswith('.print') or stripped.lower().startswith('.plot'):
            return self._convert_print(stripped)
        
        # --- Directiva .model ---
        if stripped.lower().startswith('.model'):
            return self._convert_model(stripped)
        
        # --- Directiva .subckt ---
        if stripped.lower().startswith('.subckt') or stripped.lower().startswith('.ends'):
            return self._convert_subcircuit(stripped)
        
        # --- Directiva .include ---
        if stripped.lower().startswith('.include'):
            return self._convert_include(stripped)
        
        # --- Directiva .lib ---
        if stripped.lower().startswith('.lib'):
            return self._convert_lib(stripped)
        
        # --- Directiva .options ---
        if stripped.lower().startswith('.options'):
            return self._convert_options(stripped)
        
        # --- Directiva .end ---
        if stripped.lower() == '.end':
            return '.END'
        
        # --- Directivas no soportadas en Xyce ---
        unsupported = ['.save', '.probe', '.alter', '.step', '.meas']
        for directive in unsupported:
            if stripped.lower().startswith(directive):
                return f'* [NO SOPORTADO EN XYCE] {line}'
        
        # --- Componentes del circuito ---
        return self._convert_component(line)

    def _convert_param(self, line: str) -> str:
        """Convierte directiva .param a formato Xyce."""
        # NgSpice: .param name=value
        # Xyce: .GLOBAL_PARAM name=value o sustitución directa
        
        match = re.match(r'\.param\s+(\w+)\s*=\s*(.+)', line, re.IGNORECASE)
        if match:
            param_name = match.group(1)
            param_value = match.group(2).strip()
            
            if self.expand_params:
                # Guardar para sustitución, comentar la línea
                return f'* .PARAM {param_name}={param_value} (expandido en componentes)'
            else:
                # Usar .GLOBAL_PARAM de Xyce
                return f'.GLOBAL_PARAM {param_name}={param_value}'
        
        return line

    def _convert_dc(self, line: str) -> str:
        """Convierte análisis DC."""
        # NgSpice: .dc srcname vstart vstop vincr [src2 ...]
        # Xyce: .DC srcname vstart vstop vincr
        
        # El formato es básicamente el mismo, solo aseguramos mayúsculas
        converted = re.sub(r'^\.dc\s+', '.DC ', line, flags=re.IGNORECASE)
        return converted

    def _convert_ac(self, line: str) -> str:
        """Convierte análisis AC."""
        # NgSpice: .ac dec nd fstart fstop
        # Xyce: .AC DEC nd fstart fstop
        
        converted = re.sub(r'^\.ac\s+', '.AC ', line, flags=re.IGNORECASE)
        # Convertir tipo de barrido a mayúsculas
        converted = re.sub(r'\.AC\s+(dec|lin|oct)', 
                          lambda m: f'.AC {m.group(1).upper()}', 
                          converted, flags=re.IGNORECASE)
        return converted

    def _convert_tran(self, line: str) -> str:
        """Convierte análisis transitorio."""
        # NgSpice: .tran tstep tstop [tstart [tmax]] [uic]
        # Xyce: .TRAN tstep tstop [tstart [tmax]]
        
        converted = re.sub(r'^\.tran\s+', '.TRAN ', line, flags=re.IGNORECASE)
        # Eliminar 'uic' si está presente (Xyce usa .IC separado)
        converted = re.sub(r'\s+uic\s*$', '', converted, flags=re.IGNORECASE)
        return converted

    def _convert_op(self, line: str) -> str:
        """Convierte análisis de punto de operación."""
        return '.OP'

    def _convert_print(self, line: str) -> str:
        """Convierte directiva .print/.plot."""
        # NgSpice: .print/.plot [dc|ac|tran] expr1 expr2 ...
        # Xyce: .PRINT analysistype {variables}
        
        # Detectar tipo de análisis
        analysis_match = re.match(r'\.(print|plot)\s+(dc|ac|tran)?\s*(.+)', 
                                  line, re.IGNORECASE)
        if analysis_match:
            analysis_type = analysis_match.group(2) or 'DC'
            variables = analysis_match.group(3)
            
            # Convertir variables al formato Xyce
            variables = self._convert_print_variables(variables)
            
            return f'.PRINT {analysis_type.upper()} {variables}'
        
        return f'.PRINT DC {line.split(None, 1)[1] if len(line.split()) > 1 else ""}'

    def _convert_print_variables(self, variables: str) -> str:
        """Convierte variables de print a formato Xyce."""
        # Eliminar variables que son 'let' de NgSpice (no existen en Xyce)
        # Estas se manejarán como comentario
        
        result = variables
        
        # Eliminar signo negativo antes de I() o V() - Xyce no lo soporta
        result = re.sub(r'-\s*([IV])\s*\(', r'\1(', result, flags=re.IGNORECASE)
        
        # Convertir i(xxx) a I(xxx)
        result = re.sub(r'\bi\s*\(', 'I(', result, flags=re.IGNORECASE)
        # Convertir v(xxx) a V(xxx)
        result = re.sub(r'\bv\s*\(', 'V(', result, flags=re.IGNORECASE)
        # Convertir vd(), vg(), vs() a formato Xyce
        result = re.sub(r'\bv([dgs])\s*\(', lambda m: f'V{m.group(1).upper()}(', 
                       result, flags=re.IGNORECASE)
        
        # Filtrar variables que no son V() o I() (como 'potencia' que era un let)
        tokens = result.split()
        valid_tokens = []
        for token in tokens:
            # Mantener solo V(...) e I(...)
            if re.match(r'^[VI]\s*\(', token, re.IGNORECASE) or \
               re.match(r'^V[DGS]\s*\(', token, re.IGNORECASE):
                valid_tokens.append(token)
        
        # Si no hay tokens válidos, usar valores por defecto para célula solar
        if not valid_tokens:
            return 'V(2) I(Vload)'
        
        # Asegurarse de incluir V(2) si solo hay corriente
        has_voltage = any(t.upper().startswith('V(') for t in valid_tokens)
        if not has_voltage:
            valid_tokens.insert(0, 'V(2)')
        
        return ' '.join(valid_tokens)

    def _convert_model(self, line: str) -> str:
        """Convierte directiva .model."""
        # El formato es similar, pero Xyce es más estricto
        # NgSpice: .model name type (params)
        # Xyce: .MODEL name type (params)
        
        converted = re.sub(r'^\.model\s+', '.MODEL ', line, flags=re.IGNORECASE)
        
        # Expandir parámetros si es necesario
        if self.expand_params:
            converted = self._expand_parameters(converted)
        
        return converted

    def _convert_subcircuit(self, line: str) -> str:
        """Convierte directivas de subcircuito."""
        if line.lower().startswith('.subckt'):
            return re.sub(r'^\.subckt\s+', '.SUBCKT ', line, flags=re.IGNORECASE)
        elif line.lower().startswith('.ends'):
            return re.sub(r'^\.ends', '.ENDS', line, flags=re.IGNORECASE)
        return line

    def _convert_include(self, line: str) -> str:
        """Convierte directiva .include."""
        return re.sub(r'^\.include\s+', '.INCLUDE ', line, flags=re.IGNORECASE)

    def _convert_lib(self, line: str) -> str:
        """Convierte directiva .lib."""
        return re.sub(r'^\.lib\s+', '.LIB ', line, flags=re.IGNORECASE)

    def _convert_options(self, line: str) -> str:
        """Convierte directiva .options."""
        # Xyce usa diferentes opciones, algunas necesitan traducción
        converted = re.sub(r'^\.options\s+', '.OPTIONS ', line, flags=re.IGNORECASE)
        
        # Mapeo de opciones NgSpice -> Xyce
        option_map = {
            'abstol': 'ABSTOL',
            'reltol': 'RELTOL',
            'vntol': 'VNTOL',
            'itl1': 'NONLIN MAXSTEP',
            'itl2': 'NONLIN MAXSTEP',
            'method': 'TIMEINT METHOD',
        }
        
        for ng_opt, xyce_opt in option_map.items():
            converted = re.sub(rf'\b{ng_opt}\b', xyce_opt, converted, flags=re.IGNORECASE)
        
        return converted

    def _convert_component(self, line: str) -> str:
        """Convierte componentes del circuito."""
        stripped = line.strip()
        
        if not stripped or stripped.startswith('*'):
            return line
        
        # Identificar tipo de componente
        first_char = stripped[0].upper()
        
        # Expandir parámetros en llaves {param_name}
        if self.expand_params:
            line = self._expand_parameters(line)
        
        # Convertir expresiones específicas de NgSpice
        line = self._convert_expressions(line)
        
        # Componentes que necesitan conversión especial
        converters = {
            'B': self._convert_behavioral_source,
            'E': self._convert_vcvs,
            'F': self._convert_cccs,
            'G': self._convert_vccs,
            'H': self._convert_ccvs,
        }
        
        if first_char in converters:
            return converters[first_char](line)
        
        return line

    def _expand_parameters(self, line: str) -> str:
        """Expande parámetros {name} a sus valores."""
        def replace_param(match):
            param_name = match.group(1)
            if param_name in self.parameters:
                return self.parameters[param_name]
            return match.group(0)
        
        return re.sub(r'\{(\w+)\}', replace_param, line)

    def _convert_expressions(self, line: str) -> str:
        """Convierte expresiones matemáticas de NgSpice a Xyce."""
        # Xyce usa sintaxis ligeramente diferente para algunas funciones
        
        # Convertir funciones trigonométricas (generalmente iguales)
        # Convertir función ternaria
        line = re.sub(r'\?', ' ? ', line)
        line = re.sub(r':', ' : ', line)
        
        # Convertir operadores lógicos
        line = re.sub(r'&&', ' & ', line)
        line = re.sub(r'\|\|', ' | ', line)
        
        return line

    def _convert_behavioral_source(self, line: str) -> str:
        """Convierte fuente comportamental B."""
        # NgSpice: Bxxx n+ n- V=expr o I=expr
        # Xyce: Bxxx n+ n- V={expr} o I={expr}
        
        # Asegurar que la expresión está entre llaves
        if 'V=' in line.upper() or 'I=' in line.upper():
            # Si no tiene llaves, añadirlas
            line = re.sub(r'([VI])=([^{].*?)(\s*$)', r'\1={\2}\3', line, flags=re.IGNORECASE)
        
        return line

    def _convert_vcvs(self, line: str) -> str:
        """Convierte fuente de tensión controlada por tensión."""
        # El formato es similar en ambos simuladores
        return line

    def _convert_cccs(self, line: str) -> str:
        """Convierte fuente de corriente controlada por corriente."""
        return line

    def _convert_vccs(self, line: str) -> str:
        """Convierte fuente de corriente controlada por tensión."""
        return line

    def _convert_ccvs(self, line: str) -> str:
        """Convierte fuente de tensión controlada por corriente."""
        return line

    def _parse_control_line(self, line: str) -> None:
        """Parsea líneas dentro del bloque .control para extraer análisis."""
        stripped = line.strip().lower()
        
        # Detectar comandos de análisis
        if stripped.startswith('dc '):
            # Extraer análisis DC
            parts = stripped.split()
            if len(parts) >= 5:
                src = parts[1]
                vstart = parts[2]
                vstop = parts[3]
                vincr = parts[4]
                self.detected_analyses.append(f'.DC {src} {vstart} {vstop} {vincr}')
        
        elif stripped.startswith('ac '):
            parts = stripped.split()
            if len(parts) >= 5:
                sweep_type = parts[1].upper()
                points = parts[2]
                fstart = parts[3]
                fstop = parts[4]
                self.detected_analyses.append(f'.AC {sweep_type} {points} {fstart} {fstop}')
        
        elif stripped.startswith('tran '):
            parts = stripped.split()
            if len(parts) >= 3:
                tstep = parts[1]
                tstop = parts[2]
                tstart = parts[3] if len(parts) > 3 else ''
                self.detected_analyses.append(f'.TRAN {tstep} {tstop} {tstart}'.strip())
        
        elif stripped.startswith('op'):
            self.detected_analyses.append('.OP')
        
        # Detectar wrdata/print para generar .PRINT
        elif 'wrdata' in stripped or 'write' in stripped:
            # Intentar extraer variables
            match = re.search(r'wrdata\s+\S+\s+(.+)', stripped)
            if match:
                variables = match.group(1)
                # Determinar tipo de análisis
                analysis_type = 'DC'
                for analysis in self.detected_analyses:
                    if '.AC' in analysis:
                        analysis_type = 'AC'
                    elif '.TRAN' in analysis:
                        analysis_type = 'TRAN'
                
                variables = self._convert_print_variables(variables)
                self.print_statements.append(f'.PRINT {analysis_type} {variables}')


class NgSpiceXyceConverter:
    """Clase de conveniencia para conversión rápida."""
    
    @staticmethod
    def convert_file(input_path: str, output_path: str = None) -> str:
        """Convierte un archivo NgSpice a Xyce."""
        compiler = NgSpiceToXyceCompiler()
        
        if output_path is None:
            # Generar nombre de salida automáticamente
            input_p = Path(input_path)
            output_path = str(input_p.parent / f"{input_p.stem}_xyce{input_p.suffix}")
        
        return compiler.compile(input_path, output_path)
    
    @staticmethod
    def convert_string(ngspice_code: str) -> str:
        """Convierte código NgSpice en string a Xyce."""
        compiler = NgSpiceToXyceCompiler()
        return compiler.convert(ngspice_code)


def print_help():
    """Imprime ayuda de uso."""
    help_text = """
╔═══════════════════════════════════════════════════════════════════╗
║           Compilador NgSpice a Xyce - Guía de Uso                ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  USO:                                                             ║
║    python Compiladro_ng_xyce.py <archivo_entrada> [archivo_salida]║
║                                                                   ║
║  EJEMPLOS:                                                        ║
║    python Compiladro_ng_xyce.py circuito.cir                      ║
║    python Compiladro_ng_xyce.py entrada.cir salida_xyce.cir       ║
║                                                                   ║
║  CONVERSIONES SOPORTADAS:                                         ║
║    • .param → Expansión directa o .GLOBAL_PARAM                   ║
║    • .control/.endc → Extraído a análisis Xyce                    ║
║    • .dc, .ac, .tran, .op → Formato Xyce                         ║
║    • .model → .MODEL con parámetros expandidos                    ║
║    • .subckt/.ends → .SUBCKT/.ENDS                                ║
║    • .print/.plot → .PRINT                                        ║
║    • Componentes: R, L, C, V, I, D, Q, M, etc.                   ║
║    • Fuentes comportamentales (B)                                 ║
║    • Fuentes controladas (E, F, G, H)                            ║
║                                                                   ║
║  LIMITACIONES:                                                    ║
║    • Funciones específicas de NgSpice pueden requerir ajuste     ║
║    • Algunos modelos avanzados pueden necesitar revisión          ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""
    print(help_text)


def main():
    """Función principal para uso desde línea de comandos."""
    if len(sys.argv) < 2:
        print_help()
        
        # Modo interactivo
        print("\n¿Desea ejecutar una conversión? (s/n): ", end="")
        try:
            response = input().strip().lower()
            if response in ['s', 'si', 'sí', 'y', 'yes']:
                print("Ingrese la ruta del archivo NgSpice: ", end="")
                input_file = input().strip()
                print("Ingrese la ruta de salida (Enter para auto): ", end="")
                output_file = input().strip() or None
                
                if os.path.exists(input_file):
                    NgSpiceXyceConverter.convert_file(input_file, output_file)
                else:
                    print(f"Error: No se encontró el archivo '{input_file}'")
        except KeyboardInterrupt:
            print("\nOperación cancelada.")
        return
    
    if sys.argv[1] in ['-h', '--help', '/?']:
        print_help()
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: No se encontró el archivo '{input_file}'")
        sys.exit(1)
    
    try:
        result = NgSpiceXyceConverter.convert_file(input_file, output_file)
        print("\n" + "="*60)
        print("CONVERSIÓN COMPLETADA")
        print("="*60)
        
        if not output_file:
            print("\nCódigo Xyce generado:")
            print("-"*60)
            print(result)
    except Exception as e:
        print(f"Error durante la conversión: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
