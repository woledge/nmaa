/** @odoo-module **/

import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { ScannerAudio } from "./scanner_audio";

export class BarcodeScannerDialog extends Component {
  static template = "sale_barcode_scanner.BarcodeScannerDialog";
  static components = { Dialog };
  static props = {
    close: Function,
    orderId: Number,
  };

  setup() {
    this.orm = useService("orm");
    this.notification = useService("notification");
    this.state = useState({
      scanning: false,
      lastScannedProduct: null,
      cameraActive: false,
      manualBarcode: "",
    });
    this.videoRef = useRef("videoElement");
    this.stream = null;
    this.scanInterval = null;
    this.lastScannedBarcode = null;
    this.lastScanTime = 0;
  }

  async startCamera() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      });

      if (this.videoRef.el) {
        this.videoRef.el.srcObject = this.stream;
        this.state.cameraActive = true;
        this.state.scanning = true;

        this.startBarcodeDetection();
      }
    } catch (error) {
      this.notification.add("Camera access denied or not available. Please use manual entry.", {
        type: "warning",
      });
      console.error("Camera error:", error);
    }
  }

  stopCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
    if (this.scanInterval) {
      clearInterval(this.scanInterval);
      this.scanInterval = null;
    }
    this.state.cameraActive = false;
    this.state.scanning = false;
    this.lastScannedBarcode = null;
    this.lastScanTime = 0;
  }

  startBarcodeDetection() {
    if ("BarcodeDetector" in window) {
      const barcodeDetector = new BarcodeDetector({
        formats: ["qr_code", "ean_13", "ean_8", "code_128", "code_39", "upc_a", "upc_e"],
      });

      this.scanInterval = setInterval(async () => {
        if (this.videoRef.el && this.videoRef.el.readyState === this.videoRef.el.HAVE_ENOUGH_DATA) {
          try {
            const barcodes = await barcodeDetector.detect(this.videoRef.el);
            if (barcodes.length > 0) {
              const barcode = barcodes[0].rawValue;
              await this.processBarcode(barcode);
            }
          } catch (error) {
            console.error("Barcode detection error:", error);
          }
        }
      }, 500);
    } else {
      this.notification.add(
        "Automatic barcode detection not supported. Please enter barcode manually.",
        { type: "info" }
      );
    }
  }

  async processBarcode(barcode) {
    if (!barcode || this.state.scanning === false) return;

    const currentTime = Date.now();
    if (this.lastScannedBarcode === barcode && currentTime - this.lastScanTime < 2000) {
      console.log("Duplicate scan ignored:", barcode);
      return;
    }

    this.state.scanning = false;
    this.lastScannedBarcode = barcode;
    this.lastScanTime = currentTime;

    try {
      const result = await this.orm.call("sale.order", "add_product_by_barcode", [
        this.props.orderId,
        barcode,
      ]);

      if (result.success) {
        ScannerAudio.playSuccess();

        this.state.lastScannedProduct = result;
        this.notification.add(`Added: ${result.product_name} (Qty: ${result.quantity})`, {
          type: "success",
        });

        setTimeout(() => {
          this.state.scanning = true;
        }, 1500);
      } else {
        ScannerAudio.playError();

        this.notification.add(result.error || "Product not found", {
          type: "danger",
          title: "Scan Error",
        });

        setTimeout(() => {
          this.state.scanning = true;
          this.lastScannedBarcode = null;
        }, 2000);
      }
    } catch (error) {
      ScannerAudio.playError();

      this.notification.add(
        error.data?.message || error.message || "Failed to add product. Please try again.",
        {
          type: "danger",
          title: "Error",
        }
      );

      setTimeout(() => {
        this.state.scanning = true;
        this.lastScannedBarcode = null;
      }, 2000);
    }
  }

  async onManualBarcodeSubmit() {
    if (this.state.manualBarcode) {
      await this.processBarcode(this.state.manualBarcode);
      this.state.manualBarcode = "";
    }
  }

  onBarcodeInput(ev) {
    this.state.manualBarcode = ev.target.value;
  }

  onBarcodeKeydown(ev) {
    if (ev.key === "Enter") {
      ev.preventDefault();
      this.onManualBarcodeSubmit();
    }
  }

  close() {
    this.stopCamera();
    this.props.close();
  }
}

export class BarcodeScannerAction extends Component {
  static template = "sale_barcode_scanner.BarcodeScannerAction";
  static components = { BarcodeScannerDialog };

  setup() {
    this.action = useService("action");
    const orderId = this.props.action.context.active_id;

    this.state = useState({
      orderId: orderId,
    });
  }

  onClose() {
    this.action.doAction({ type: "ir.actions.act_window_close" });
  }
}

registry.category("actions").add("sale_barcode_scanner", BarcodeScannerAction);
