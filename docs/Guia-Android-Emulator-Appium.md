# Guia: Android Emulator + Appium (macOS Apple Silicon)

## Objetivo
Rodar o app da OLX Android localmente sem device físico, usando emulador + Appium para automação.

---

## Pré-requisitos
- macOS com Apple Silicon (M1/M2/M3/M4)
- Homebrew instalado
- APK do app OLX (pedir para um dev Android do time)

---

## Passo 1 — Instalar Android Command Line Tools

```bash
brew install --cask android-commandlinetools
```

O SDK será instalado em: `/opt/homebrew/share/android-commandlinetools`

---

## Passo 2 — Instalar Java (Temurin JDK)

O SDK Android requer Java. Instalar o Temurin (JDK open source):

```bash
brew install --cask temurin
```

---

## Passo 3 — Aceitar licenças do Android SDK

```bash
yes | sdkmanager --licenses
```

---

## Passo 4 — Instalar emulador, platform tools e imagem do sistema

```bash
sdkmanager "emulator" "platform-tools" "system-images;android-34;google_apis;arm64-v8a"
```

> **Nota:** Usar imagem `arm64-v8a` (nativa Apple Silicon). Imagens x86 são muito lentas em ARM.
> A variante `google_apis` inclui Google Play Services (necessário para apps que usam push, maps, etc.)

---

## Passo 5 — Criar o device virtual (AVD)

```bash
avdmanager create avd -n pixel7 -k "system-images;android-34;google_apis;arm64-v8a"
```

Quando perguntar sobre custom hardware profile, responder `no`.

> **Nota:** Se aparecer erro sobre `devices.xml`, ignorar — o AVD é criado mesmo assim.
> Se quiser recriar, usar `--force`: `avdmanager create avd -n pixel7 -k "..." --force`

---

## Passo 6 — Iniciar o emulador

```bash
/opt/homebrew/share/android-commandlinetools/emulator/emulator -avd pixel7
```

Uma janela com o celular virtual vai abrir. Aguardar o boot completo (home screen aparecer).

> **Dica:** O binário `emulator` não fica no PATH. Usar sempre o caminho completo acima.

---

## Passo 7 — Instalar o APK da OLX

Com o emulador rodando:

```bash
/opt/homebrew/share/android-commandlinetools/platform-tools/adb install /caminho/para/olx.apk
```

Exemplo real:
```bash
/opt/homebrew/share/android-commandlinetools/platform-tools/adb install ~/Desktop/app-release-26.21.0-15000577.apk
```

O app aparecerá na home screen do emulador.

---

## Passo 8 — Verificar conexão ADB

```bash
/opt/homebrew/share/android-commandlinetools/platform-tools/adb devices
```

Deve mostrar algo como:
```
List of devices attached
emulator-5554   device
```

---

## Usando com Appium (automação via Kiro CLI)

O Kiro CLI tem o Appium MCP integrado. Para conectar ao emulador:

1. Garantir que o emulador está rodando (`emulator -avd pixel7`)
2. No Kiro CLI, usar `select_device` com platform `android`
3. Criar sessão Appium com `appium_session_management` (action=create)
4. Usar `appium_find_element`, `appium_gesture`, `appium_screenshot` etc. para interagir

---

## Como obter o APK da OLX

| Fonte | Como |
|-------|------|
| **Dev do time** | Pedir APK de debug/staging (Enzo, Kevin, Lucas Justino) |
| **CI/CD** | Baixar build recente do pipeline (Firebase App Distribution, Bitrise) |
| **Play Store** | Baixar de APKMirror (versão produção, sem debug) |
| **Device físico** | `adb shell pm path com.olx.olx` → `adb pull <path> olx.apk` |

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| `command not found: emulator` | Usar path completo: `/opt/homebrew/share/android-commandlinetools/emulator/emulator` |
| `command not found: sdkmanager` | Fechar e reabrir o terminal após `brew install` |
| `Unable to locate a Java Runtime` | Instalar Java: `brew install --cask temurin` |
| `Error: Could not load devices from devices.xml` | Ignorar — AVD é criado. Ou usar sem flag `-d` |
| `AVD already exists` | Usar `--force` para recriar, ou rodar direto `emulator -avd pixel7` |
| Emulador muito lento | Verificar se está usando imagem `arm64-v8a` (não x86) |
| App crash no emulador | Verificar se o APK é compatível com `arm64`. APKs "universal" funcionam |

---

## Paths importantes

| O quê | Caminho |
|-------|---------|
| SDK root | `/opt/homebrew/share/android-commandlinetools` |
| Emulator | `/opt/homebrew/share/android-commandlinetools/emulator/emulator` |
| ADB | `/opt/homebrew/share/android-commandlinetools/platform-tools/adb` |
| AVD Manager | `/opt/homebrew/bin/avdmanager` |
| SDK Manager | `/opt/homebrew/bin/sdkmanager` |
| AVDs salvos | `~/.android/avd/` |

---

## Referências
- [Android Command Line Tools](https://developer.android.com/tools)
- [Appium MCP (Kiro CLI)](https://github.com/anthropics/appium-mcp)
- Data: 31/07/2026
