/**
 * Web Serial API 类型定义
 * 基于 W3C Web Serial API 规范
 */

declare global {
  interface Navigator {
    serial: Serial
  }

  interface Serial {
    requestPort(options?: SerialPortRequestOptions): Promise<SerialPort>
    getPorts(): Promise<SerialPort[]>
    onconnect: ((this: Serial, ev: Event) => any) | null
    ondisconnect: ((this: Serial, ev: Event) => any) | null
    addEventListener(type: 'connect' | 'disconnect', listener: (this: Serial, ev: Event) => any, useCapture?: boolean): void
    removeEventListener(type: 'connect' | 'disconnect', listener: (this: Serial, ev: Event) => any, useCapture?: boolean): void
  }

  interface SerialPortRequestOptions {
    filters?: SerialPortFilter[]
  }

  interface SerialPortFilter {
    usbVendorId?: number
    usbProductId?: number
  }

  interface SerialPort {
    readonly readable: ReadableStream<Uint8Array> | null
    readonly writable: WritableStream<Uint8Array> | null
    open(options: SerialPortOpenOptions): Promise<void>
    close(): Promise<void>
    getInfo(): SerialPortInfo
    addEventListener(type: 'connect' | 'disconnect', listener: (this: SerialPort, ev: Event) => any, useCapture?: boolean): void
    removeEventListener(type: 'connect' | 'disconnect', listener: (this: SerialPort, ev: Event) => any, useCapture?: boolean): void
  }

  interface SerialPortOpenOptions {
    baudRate: number
    dataBits?: 7 | 8
    parity?: 'none' | 'even' | 'odd'
    stopBits?: 1 | 2
    flowControl?: 'none' | 'hardware'
    bufferSize?: number
  }

  interface SerialPortInfo {
    usbVendorId?: number
    usbProductId?: number
  }
}

export {}
