import os
import subprocess
import sys

class PiConversionLib:
    """Library wrapper for BMP/PI conversion using bmp2pi lib by MIYASAKA Masaru."""
    
    def __init__(self, bmp2pi_exe=None, pi2bmp_exe=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.bmp2pi_path = bmp2pi_exe or os.path.join(base_dir, 'bmp2pi.exe')
        self.pi2bmp_path = pi2bmp_exe or os.path.join(base_dir, 'pi2bmp.exe')
        
        if not os.path.exists(self.bmp2pi_path):
            raise FileNotFoundError(f"bmp2pi.exe not found at {self.bmp2pi_path}")
        if not os.path.exists(self.pi2bmp_path):
            raise FileNotFoundError(f"pi2bmp.exe not found at {self.pi2bmp_path}")
    
    def bmp_to_pi(self, bmp_file, pi_file):
        """
        Convert BMP file to PI format.
        
        Command line:
            bmp2pi.exe -o <pi_file> <bmp_file>
        """
        if not os.path.exists(bmp_file):
            print(f"Error: Input file {bmp_file} not found")
            return 1
        
        try:
            result = subprocess.run(
                [self.bmp2pi_path, '-o', pi_file, bmp_file],
                capture_output=True,
                timeout=30
            )
            
            return result.returncode
        except subprocess.TimeoutExpired:
            print(f"Error: BMP to PI conversion timeout for {bmp_file}")
            return 1
        except Exception as e:
            print(f"Error converting BMP to PI: {e}")
            return 1
    
    def pi_to_bmp(self, pi_file, bmp_file):
        """
        Convert PI file to BMP format.
        
        Command line:
            pi2bmp.exe -o <bmp_file> <pi_file>
        """
        if not os.path.exists(pi_file):
            print(f"Error: Input file {pi_file} not found")
            return 1
        
        try:
            result = subprocess.run(
                [self.pi2bmp_path, '-o', bmp_file, pi_file],
                capture_output=True,
                timeout=30
            )
            
            return result.returncode
        except subprocess.TimeoutExpired:
            print(f"Error: PI to BMP conversion timeout for {pi_file}")
            return 1
        except Exception as e:
            print(f"Error converting PI to BMP: {e}")
            return 1

# Global instance for convenience
try:
    lib = PiConversionLib()
except FileNotFoundError as e:
    print(f"Warning: {e}")
    lib = None

# Conversion functions (convenience wrappers)
def bmp_to_pi(bmp_file, pi_file):
    if lib is None:
        print("Error: Conversion library not initialized")
        return 1
    return lib.bmp_to_pi(bmp_file, pi_file)

def pi_to_bmp(pi_file, bmp_file):
    """Convert PI file to BMP format."""
    if lib is None:
        print("Error: Conversion library not initialized")
        return 1
    return lib.pi_to_bmp(pi_file, bmp_file)
