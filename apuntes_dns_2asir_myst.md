---
title: Apuntes DNS (2º ASIR) — versión MyST
source_notebook: apuntes_dns_2asir_con_30_qseeds.ipynb
---

# DNS: Sistema de Nombres de Dominio

**Módulo:** Servicios en Red e Internet  
**Ciclo:** 2.º ASIR  
**Unidad:** Instalación y administración de servicios de nombres de dominio  
**Versión:** 1.0  
**Fecha:** 13/05/2026

Este cuaderno reúne los apuntes básicos y prácticos sobre DNS. Está pensado para trabajar primero los conceptos y después aplicarlos en un laboratorio con **Ubuntu Server + BIND9** y **Windows Server DNS**.


## 1. Objetivos de aprendizaje

Al finalizar esta unidad deberías ser capaz de:

1. Explicar qué problema resuelve DNS y por qué es necesario en redes TCP/IP.
2. Diferenciar entre cliente DNS, resolutor, servidor recursivo y servidor autoritativo.
3. Comprender la estructura jerárquica de nombres: raíz, TLD, dominio, subdominio y FQDN.
4. Interpretar registros DNS habituales: `A`, `AAAA`, `CNAME`, `MX`, `NS`, `SOA`, `PTR`, `TXT`, `SRV` y `CAA`.
5. Configurar una zona directa e inversa en un servidor DNS Linux con BIND9.
6. Configurar zonas y registros básicos en Windows Server DNS.
7. Utilizar reenviadores, caché y transferencias de zona.
8. Diagnosticar problemas de resolución con herramientas como `dig`, `nslookup`, `host`, `resolvectl` y `Resolve-DnsName`.
9. Documentar la instalación y configuración de un servicio DNS con evidencias de funcionamiento.


## 2. Relación con los criterios de evaluación

Esta unidad se relaciona especialmente con el resultado de aprendizaje:

> **Administra servicios de resolución de nombres, analizándolos y garantizando la seguridad del servicio.**

Criterios trabajados:

- Identificación de escenarios donde se necesita resolución de nombres.
- Clasificación de mecanismos de resolución de nombres.
- Descripción de la estructura jerárquica del sistema DNS.
- Instalación y configuración de servicios DNS.
- Configuración de reenviadores y caché.
- Creación de registros DNS de una zona.
- Configuración de resolución inversa.
- Transferencias de zona entre servidores.
- Documentación del procedimiento de instalación, configuración y pruebas.


## 3. Caso de partida: TechServe S.A.

Vamos a utilizar una empresa ficticia llamada **TechServe S.A.**. La empresa tiene varios servicios internos:

| Servicio | Nombre DNS | Dirección IP |
|---|---:|---:|
| Servidor DNS Linux | `ns1.techserve.test` | `192.168.56.10` |
| Servidor DNS Windows | `ns2.techserve.test` | `192.168.56.20` |
| Servidor web | `www.techserve.test` | `192.168.56.30` |
| Servidor de correo | `mail.techserve.test` | `192.168.56.40` |
| Servidor FTP | `ftp.techserve.test` | Alias de `www.techserve.test` |

Usaremos el dominio **`techserve.test`** porque `.test` está reservado para pruebas y documentación. En un entorno real se usaría un dominio registrado o un subdominio controlado por la organización.

> **Nota:** en prácticas antiguas es frecuente ver dominios internos terminados en `.local`, pero puede generar conflictos con mDNS/Bonjour/Avahi. Para prácticas de aula es preferible utilizar dominios reservados para pruebas, como `.test`, o un subdominio propio.


## 4. ¿Qué es DNS?

**DNS** significa **Domain Name System** o **Sistema de Nombres de Dominio**.

Su función principal es traducir nombres fáciles de recordar a direcciones IP.

Por ejemplo:

```text
www.ejemplo.com  →  93.184.216.34
```

Los ordenadores se comunican mediante direcciones IP, pero las personas recordamos mejor nombres. DNS actúa como un sistema distribuido que permite localizar servicios en Internet o dentro de una red local.

DNS no solo resuelve nombres de páginas web. También se usa para:

- Localizar servidores de correo.
- Identificar controladores de dominio en Active Directory.
- Publicar políticas de correo como SPF, DKIM o DMARC.
- Resolver nombres internos de una empresa.
- Permitir alias de servicios.
- Hacer resolución inversa de IP a nombre.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-what-is
:type: mcq
:n: 2
:difficulty: media
:objective: Definir DNS y su función principal

DNS (Domain Name System) traduce nombres de dominio legibles por humanos a direcciones IP para poder localizar servicios en la red.
:::


## 5. Antes de DNS: ficheros `hosts`

Antes de usar DNS, un equipo puede resolver nombres mediante un fichero local llamado `hosts`.

En Linux:

```text
/etc/hosts
```

En Windows:

```text
C:\Windows\System32\drivers\etc\hosts
```

Ejemplo:

```text
192.168.56.30    www.techserve.test
192.168.56.40    mail.techserve.test
```

### Ventajas del fichero `hosts`

- Es sencillo.
- No necesita servidor DNS.
- Puede servir para pruebas puntuales.

### Inconvenientes

- No escala bien.
- Hay que modificarlo equipo por equipo.
- Es fácil que quede desactualizado.
- No permite delegación ni administración centralizada.

Por eso, en redes medianas o grandes se utiliza DNS.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-hosts-file
:type: mcq
:n: 2
:difficulty: media
:objective: Explicar el fichero hosts y sus limitaciones

Antes de DNS, la resolución de nombres podía hacerse mediante un fichero local hosts que asocia nombres a direcciones IP, pero no escala bien y requiere mantenimiento manual.
:::


## 6. Estructura jerárquica del DNS

DNS se organiza como un árbol invertido.

```text
.                         ← raíz
├── com                   ← TLD
│   └── ejemplo           ← dominio de segundo nivel
│       └── www           ← host o subdominio
├── org
├── net
└── es
    └── educa
        └── www
```

Un nombre completo como:

```text
www.techserve.test.
```

se denomina **FQDN**: **Fully Qualified Domain Name**.

El punto final representa la raíz DNS. Normalmente no lo escribimos, pero técnicamente forma parte del nombre completo.

| Elemento | Ejemplo | Explicación |
|---|---|---|
| Raíz | `.` | Nivel superior de la jerarquía DNS. |
| TLD | `.com`, `.es`, `.org`, `.test` | Dominio de nivel superior. |
| Dominio | `techserve.test` | Nombre gestionado por una organización. |
| Subdominio | `aula.techserve.test` | División interna del dominio. |
| Host | `www.techserve.test` | Nombre de un equipo o servicio concreto. |


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-hierarchy
:type: mcq
:n: 2
:difficulty: media
:objective: Describir la estructura jerárquica del DNS

DNS se organiza como una jerarquía en forma de árbol invertido con una raíz (.) y dominios de nivel superior (TLD) como .com o .es, delegando autoridad a niveles inferiores.
:::


## 7. Componentes que intervienen en una consulta DNS

En una resolución DNS pueden intervenir varios elementos:

| Componente | Función |
|---|---|
| **Cliente DNS** | Equipo que necesita resolver un nombre. |
| **Stub resolver** | Parte del sistema operativo que envía la consulta DNS. |
| **Servidor recursivo** | Recibe la consulta del cliente y busca la respuesta completa. |
| **Servidor raíz** | Indica qué servidores conocen cada TLD. |
| **Servidor TLD** | Indica qué servidores conocen un dominio concreto. |
| **Servidor autoritativo** | Tiene la información oficial de una zona DNS. |

Ejemplo simplificado:

```text
Cliente → DNS recursivo → raíz → TLD → autoritativo → respuesta
```

El cliente normalmente no pregunta directamente a todos los servidores. Suele preguntar a su DNS configurado, por ejemplo el DNS del centro, de la empresa, del router o del proveedor.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-components
:type: mcq
:n: 2
:difficulty: media
:objective: Identificar componentes de una consulta DNS

En una consulta DNS intervienen el cliente (stub resolver), el resolvedor recursivo y los servidores autoritativos, que proporcionan la respuesta final para una zona.
:::


## 8. Resolución recursiva e iterativa

### Consulta recursiva

El cliente pide al servidor DNS una respuesta completa.

```text
Cliente: ¿Cuál es la IP de www.ejemplo.com?
DNS: Es 93.184.216.34.
```

El servidor DNS se encarga de hacer las consultas necesarias para obtener la respuesta.

### Consulta iterativa

Un servidor pregunta a otro, pero este no tiene por qué devolver la respuesta final. Puede devolver una referencia al siguiente servidor.

```text
DNS raíz: no sé la IP final, pero pregunta a los servidores de .com.
Servidor .com: no sé la IP final, pero pregunta al autoritativo de ejemplo.com.
Servidor autoritativo: la IP es 93.184.216.34.
```

### Esquema del proceso

```text
1. El cliente pregunta a su DNS recursivo.
2. El DNS recursivo pregunta a un servidor raíz.
3. El raíz indica los servidores del TLD.
4. El TLD indica los servidores autoritativos del dominio.
5. El autoritativo devuelve el registro solicitado.
6. El DNS recursivo guarda la respuesta en caché.
7. El DNS recursivo responde al cliente.
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-recursive-iterative
:type: tf
:n: 2
:difficulty: media
:objective: Diferenciar resolución recursiva e iterativa

En resolución recursiva, el resolvedor realiza las consultas necesarias hasta obtener la respuesta final; en resolución iterativa, cada servidor devuelve una referencia al siguiente servidor a consultar.
:::


## 9. Caché y TTL

DNS utiliza caché para mejorar el rendimiento.

Cuando un servidor DNS obtiene una respuesta, puede guardarla temporalmente. Así, si otro cliente pregunta por el mismo nombre, puede responder sin repetir todo el proceso.

El tiempo que una respuesta puede permanecer en caché se llama **TTL**: **Time To Live**.

Ejemplo:

```text
www.techserve.test.    3600    IN    A    192.168.56.30
```

En este caso, el TTL es `3600` segundos, es decir, 1 hora.

### Consecuencias prácticas del TTL

- Un TTL alto reduce consultas y mejora rendimiento.
- Un TTL bajo permite que los cambios se propaguen más rápido.
- Si cambiamos una IP, puede tardar en verse el cambio por culpa de la caché.
- Para migraciones, conviene bajar el TTL antes del cambio.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-cache-ttl
:type: tf
:n: 2
:difficulty: media
:objective: Comprender caché y TTL

Los resolvedores almacenan respuestas DNS en caché durante un tiempo determinado por el TTL (Time To Live), lo que reduce latencia y carga pero puede retrasar la propagación de cambios.
:::


## 10. Zonas DNS

Una **zona DNS** es una parte del espacio de nombres administrada por un servidor DNS.

Por ejemplo, si administramos:

```text
techserve.test
```

podemos tener una zona que contenga registros como:

```text
www.techserve.test
mail.techserve.test
ftp.techserve.test
```

### Tipos habituales de zona

| Tipo de zona | Descripción |
|---|---|
| **Zona primaria** | Contiene la copia editable de la zona. |
| **Zona secundaria** | Copia de solo lectura obtenida desde otro servidor mediante transferencia de zona. |
| **Zona directa** | Resuelve nombres a direcciones IP. |
| **Zona inversa** | Resuelve direcciones IP a nombres. |
| **Zona integrada en Active Directory** | Zona almacenada y replicada mediante AD DS. |
| **Zona de reenvío** | Reenvía consultas de un dominio a otros servidores. |

En BIND moderno también se usan los términos **primary** y **secondary**. En documentación o configuraciones antiguas puede aparecer **master** y **slave**.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-zones
:type: mcq
:n: 2
:difficulty: media
:objective: Explicar qué es una zona DNS

Una zona DNS es una porción del espacio de nombres gestionada por un servidor autoritativo, y puede ser primaria (maestra) o secundaria (réplica obtenida por transferencia).
:::


## 11. Registros DNS más importantes

Los registros DNS son entradas dentro de una zona. Cada registro tiene un tipo y una función.

| Registro | Función | Ejemplo |
|---|---|---|
| `A` | Asocia nombre con IPv4. | `www IN A 192.168.56.30` |
| `AAAA` | Asocia nombre con IPv6. | `www IN AAAA 2001:db8::10` |
| `CNAME` | Crea un alias. | `ftp IN CNAME www` |
| `MX` | Indica servidor de correo. | `@ IN MX 10 mail.techserve.test.` |
| `NS` | Indica servidores DNS autoritativos. | `@ IN NS ns1.techserve.test.` |
| `SOA` | Registro de autoridad de la zona. | Define servidor principal, serial y tiempos. |
| `PTR` | Resolución inversa: IP a nombre. | `30 IN PTR www.techserve.test.` |
| `TXT` | Texto asociado al dominio. | SPF, verificaciones, DKIM, DMARC. |
| `SRV` | Localiza servicios concretos. | Muy usado por Active Directory. |
| `CAA` | Indica qué CA puede emitir certificados para el dominio. | `@ IN CAA 0 issue "letsencrypt.org"` |

### Registro `A`

```text
www    IN    A    192.168.56.30
```

Resuelve `www.techserve.test` a `192.168.56.30`.

### Registro `CNAME`

```text
ftp    IN    CNAME    www
```

`ftp.techserve.test` será un alias de `www.techserve.test`.

### Registro `MX`

```text
@      IN    MX    10 mail.techserve.test.
```

Indica que el correo del dominio se entrega al servidor `mail.techserve.test`. El número `10` es la prioridad. Cuanto menor es el número, mayor es la prioridad.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-records-overview
:type: mcq
:n: 2
:difficulty: media
:objective: Reconocer registros DNS comunes

Los registros DNS describen información de una zona, como A/AAAA (direcciones), CNAME (alias), MX (correo), NS (servidores de nombres), TXT (texto) y PTR (resolución inversa).
:::


## 12. Registro SOA

El registro **SOA** significa **Start of Authority**. Es obligatorio en una zona DNS.

Ejemplo:

```text
@ IN SOA ns1.techserve.test. admin.techserve.test. (
    2026051301 ; serial
    3600       ; refresh
    1800       ; retry
    604800     ; expire
    86400      ; negative cache TTL
)
```

| Campo | Significado |
|---|---|
| Servidor primario | Servidor principal de la zona. |
| Contacto | Correo del administrador, escrito con punto en lugar de `@`. |
| Serial | Número de versión de la zona. Debe aumentar al modificar la zona. |
| Refresh | Cada cuánto pregunta un secundario si hay cambios. |
| Retry | Tiempo de espera antes de reintentar si falla la consulta. |
| Expire | Tiempo tras el cual el secundario deja de considerar válida la zona si no contacta con el primario. |
| Negative cache TTL | Tiempo de caché para respuestas negativas. |

### Sobre el serial

Una convención habitual es usar:

```text
AAAAMMDDNN
```

Por ejemplo:

```text
2026051301
```

indica la primera modificación del día 13/05/2026.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-soa-record
:type: mcq
:n: 2
:difficulty: media
:objective: Describir el registro SOA

El registro SOA (Start of Authority) define parámetros de la zona como el servidor primario, el correo del responsable y el número de serie que controla las actualizaciones.
:::


## 13. Zona directa e inversa

### Zona directa

Resuelve nombre → IP.

```text
www.techserve.test → 192.168.56.30
```

### Zona inversa

Resuelve IP → nombre.

```text
192.168.56.30 → www.techserve.test
```

Para IPv4 se utiliza el dominio especial:

```text
in-addr.arpa
```

Para la red:

```text
192.168.56.0/24
```

la zona inversa sería:

```text
56.168.192.in-addr.arpa
```

El orden de los octetos se invierte.

Registro PTR de ejemplo:

```text
30    IN    PTR    www.techserve.test.
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-forward-reverse
:type: mcq
:n: 2
:difficulty: media
:objective: Distinguir zona directa e inversa

La zona directa resuelve nombres a direcciones IP (por ejemplo, A/AAAA), mientras que la zona inversa resuelve direcciones IP a nombres mediante registros PTR.
:::


## 14. Reenviadores DNS

Un **reenviador** es un servidor DNS al que se envían consultas que el servidor local no puede resolver directamente.

Ejemplo de escenario:

- El DNS interno resuelve `techserve.test`.
- Para dominios externos como `google.com`, reenvía las consultas a otro DNS.

```text
Cliente → DNS interno → reenviador externo → Internet
```

Ejemplos de reenviadores habituales:

```text
1.1.1.1
8.8.8.8
9.9.9.9
```

En un entorno educativo conviene explicar que no se debe elegir un reenviador “porque sí”: hay que valorar privacidad, rendimiento, filtrado, política de la organización y disponibilidad.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-forwarders
:type: tf
:n: 2
:difficulty: media
:objective: Explicar qué son los reenviadores

Un reenviador DNS (forwarder) es un servidor al que se remiten consultas que no se pueden resolver localmente, para que realice la resolución en nombre del servidor.
:::


## 15. Transferencias de zona

Una **transferencia de zona** permite copiar una zona desde un servidor primario a uno secundario.

Sirve para:

- Redundancia.
- Alta disponibilidad.
- Reparto de carga.
- Continuidad del servicio si falla el DNS principal.

### Tipos de transferencia

| Tipo | Descripción |
|---|---|
| `AXFR` | Transferencia completa de la zona. |
| `IXFR` | Transferencia incremental, solo cambios. |

### Seguridad

No se deben permitir transferencias de zona a cualquier equipo. Deben restringirse a los servidores secundarios autorizados.

Ejemplo de mala práctica:

```text
allow-transfer { any; };
```

Ejemplo más seguro:

```text
allow-transfer { 192.168.56.20; };
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-zone-transfers
:type: tf
:n: 2
:difficulty: media
:objective: Comprender transferencias de zona

Las transferencias de zona permiten replicar datos desde un servidor primario a uno secundario; pueden ser completas (AXFR) o incrementales (IXFR) según el número de serie.
:::


## 16. Seguridad básica en DNS

DNS es un servicio crítico. Si DNS falla, muchos servicios dejan de funcionar aunque estén correctamente instalados.

Medidas básicas:

1. **Permitir consultas recursivas solo a clientes internos.**
2. **Restringir transferencias de zona.**
3. **No exponer información interna innecesaria.**
4. **Mantener actualizado el servidor DNS.**
5. **Registrar y revisar logs.**
6. **Separar DNS interno y externo cuando sea necesario.**
7. **Usar DNSSEC cuando el escenario lo requiera.**
8. **Usar TSIG para autenticar transferencias de zona entre servidores.**

### Errores frecuentes

- Dejar la recursión abierta a Internet.
- Permitir transferencias de zona desde cualquier IP.
- Olvidar aumentar el serial tras modificar la zona.
- No crear la zona inversa.
- Confundir un alias `CNAME` con un registro `A`.
- Usar nombres internos que entran en conflicto con dominios reales.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-basic-security
:type: tf
:n: 2
:difficulty: media
:objective: Identificar medidas básicas de seguridad DNS

Como medidas básicas, se limita la recursión a redes internas, se restringen transferencias de zona a IPs autorizadas y se aplican controles de acceso para evitar abuso.
:::


# Parte práctica: BIND9 en Ubuntu Server


## 17. Escenario de laboratorio

Usaremos esta red de práctica:

```text
Red: 192.168.56.0/24
Dominio: techserve.test

ns1.techserve.test      192.168.56.10    Ubuntu Server + BIND9
ns2.techserve.test      192.168.56.20    Windows Server DNS o segundo BIND9
www.techserve.test      192.168.56.30    Servidor web
mail.techserve.test     192.168.56.40    Servidor de correo
cliente1.techserve.test 192.168.56.100   Cliente de pruebas
```

> **Importante:** adapta las IP a tu entorno real de VirtualBox. Si utilizas una red interna o adaptador solo-anfitrión, comprueba primero la conectividad con `ping`.


## 18. Instalación de BIND9

En Ubuntu Server:

```bash
sudo apt update
sudo apt install bind9 bind9-utils dnsutils -y
```

Comprobar el estado del servicio:

```bash
systemctl status bind9
```

Comprobar que el servidor escucha en el puerto DNS:

```bash
sudo ss -tulpn | grep :53
```

DNS utiliza principalmente el puerto **53/UDP**, aunque también puede utilizar **53/TCP**, por ejemplo en transferencias de zona o respuestas grandes.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: bind-install
:type: mcq
:n: 2
:difficulty: media
:objective: Instalar BIND9 y comprobar servicio

BIND9 es una implementación de servidor DNS en Linux. Tras instalarlo, se configura como servidor autoritativo/recursivo y se verifica que el servicio named/bind9 está activo.
:::


## 19. Configuración de opciones generales

Archivo habitual:

```text
/etc/bind/named.conf.options
```

Ejemplo básico para un laboratorio interno:

```bash
sudo nano /etc/bind/named.conf.options
```

Contenido orientativo:

```text
options {
    directory "/var/cache/bind";

    recursion yes;
    allow-recursion { 192.168.56.0/24; localhost; };
    allow-query { 192.168.56.0/24; localhost; };

    forwarders {
        1.1.1.1;
        8.8.8.8;
    };

    dnssec-validation auto;

    listen-on { 192.168.56.10; 127.0.0.1; };
    listen-on-v6 { none; };
};
```

### Explicación

| Directiva | Función |
|---|---|
| `directory` | Directorio de trabajo de BIND. |
| `recursion yes` | Permite resolver nombres que no están en zonas locales. |
| `allow-recursion` | Limita quién puede usar la recursión. |
| `allow-query` | Limita quién puede consultar el servidor. |
| `forwarders` | DNS externos a los que se reenvían consultas. |
| `listen-on` | IPs donde escucha BIND. |
| `dnssec-validation auto` | Activa validación DNSSEC automática. |


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: bind-options
:type: mcq
:n: 2
:difficulty: media
:objective: Configurar opciones generales de BIND9

En BIND9, el fichero de opciones generales permite definir parámetros como recursión, reenviadores, listen-on, allow-query y allow-transfer según el escenario.
:::


## 20. Declarar las zonas en BIND9

Archivo habitual:

```text
/etc/bind/named.conf.local
```

Editamos:

```bash
sudo nano /etc/bind/named.conf.local
```

Añadimos la zona directa e inversa:

```text
zone "techserve.test" {
    type primary;
    file "/etc/bind/zones/db.techserve.test";
    allow-transfer { 192.168.56.20; };
    also-notify { 192.168.56.20; };
};

zone "56.168.192.in-addr.arpa" {
    type primary;
    file "/etc/bind/zones/db.192.168.56";
    allow-transfer { 192.168.56.20; };
    also-notify { 192.168.56.20; };
};
```

Creamos el directorio de zonas:

```bash
sudo mkdir -p /etc/bind/zones
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: bind-declare-zones
:type: mcq
:n: 2
:difficulty: media
:objective: Declarar zonas en BIND9

Para servir una zona en BIND9 se declara en la configuración (named.conf) indicando su tipo (master/slave) y el fichero de zona donde están los registros.
:::


## 21. Crear la zona directa

Creamos el archivo:

```bash
sudo nano /etc/bind/zones/db.techserve.test
```

Contenido:

```text
$TTL 86400
@   IN  SOA ns1.techserve.test. admin.techserve.test. (
        2026051301 ; serial
        3600       ; refresh
        1800       ; retry
        604800     ; expire
        86400      ; negative cache TTL
)

; Servidores DNS autoritativos
@       IN  NS      ns1.techserve.test.
@       IN  NS      ns2.techserve.test.

; Registros A
ns1     IN  A       192.168.56.10
ns2     IN  A       192.168.56.20
www     IN  A       192.168.56.30
mail    IN  A       192.168.56.40

; Alias
ftp     IN  CNAME   www.techserve.test.

; Correo
@       IN  MX 10   mail.techserve.test.

; Texto/SPF de ejemplo para laboratorio
@       IN  TXT     "v=spf1 mx -all"
```

### Observaciones importantes

- Los nombres terminados en punto son FQDN completos.
- Si no pones punto final, BIND puede completar el nombre con la zona actual.
- El serial debe aumentar cada vez que se modifica la zona.
- El registro `MX` debe apuntar a un nombre que tenga registro `A` o `AAAA`.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: bind-forward-zonefile
:type: mcq
:n: 2
:difficulty: media
:objective: Crear una zona directa en BIND9

Una zona directa en BIND9 se define en un fichero de zona con SOA, NS y registros como A/AAAA/CNAME/MX para los nombres del dominio.
:::


## 22. Crear la zona inversa

Creamos el archivo:

```bash
sudo nano /etc/bind/zones/db.192.168.56
```

Contenido:

```text
$TTL 86400
@   IN  SOA ns1.techserve.test. admin.techserve.test. (
        2026051301 ; serial
        3600       ; refresh
        1800       ; retry
        604800     ; expire
        86400      ; negative cache TTL
)

; Servidores DNS autoritativos
@       IN  NS      ns1.techserve.test.
@       IN  NS      ns2.techserve.test.

; Registros PTR
10      IN  PTR     ns1.techserve.test.
20      IN  PTR     ns2.techserve.test.
30      IN  PTR     www.techserve.test.
40      IN  PTR     mail.techserve.test.
100     IN  PTR     cliente1.techserve.test.
```

En una zona inversa `192.168.56.0/24`, el registro `30` representa la IP:

```text
192.168.56.30
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: bind-reverse-zonefile
:type: mcq
:n: 2
:difficulty: media
:objective: Crear una zona inversa en BIND9

Una zona inversa utiliza el dominio in-addr.arpa (IPv4) o ip6.arpa (IPv6) e incluye registros PTR para mapear direcciones IP a nombres.
:::


## 23. Comprobar la configuración de BIND9

Antes de reiniciar el servicio, conviene comprobar la sintaxis.

Comprobar archivos de configuración:

```bash
sudo named-checkconf
```

Comprobar la zona directa:

```bash
sudo named-checkzone techserve.test /etc/bind/zones/db.techserve.test
```

Comprobar la zona inversa:

```bash
sudo named-checkzone 56.168.192.in-addr.arpa /etc/bind/zones/db.192.168.56
```

Si todo es correcto, reiniciamos:

```bash
sudo systemctl restart bind9
sudo systemctl status bind9
```

Ver logs:

```bash
sudo journalctl -u bind9 -xe
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: bind-checkconfig
:type: mcq
:n: 2
:difficulty: media
:objective: Verificar configuración y zonas

Antes de reiniciar BIND9 conviene validar sintaxis y zonas con herramientas como named-checkconf y named-checkzone para detectar errores de configuración.
:::


## 24. Configurar un cliente Ubuntu para usar el DNS

Una forma temporal de probar el DNS es usar directamente `dig` indicando el servidor:

```bash
dig @192.168.56.10 www.techserve.test A
```

Para configurar el DNS del sistema dependerá de la versión y herramienta de red utilizada.

### Opción con `resolvectl`

Ver DNS actuales:

```bash
resolvectl status
```

Asignar DNS a una interfaz concreta, por ejemplo `enp0s3`:

```bash
sudo resolvectl dns enp0s3 192.168.56.10
sudo resolvectl domain enp0s3 techserve.test
```

### Opción con Netplan

Archivo habitual:

```text
/etc/netplan/00-installer-config.yaml
```

Ejemplo:

```yaml
network:
  version: 2
  ethernets:
    enp0s3:
      addresses:
        - 192.168.56.100/24
      nameservers:
        addresses: [192.168.56.10]
        search: [techserve.test]
```

Aplicar cambios:

```bash
sudo netplan apply
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: client-dns-config
:type: mcq
:n: 2
:difficulty: media
:objective: Configurar un cliente para usar el DNS

En un cliente, se configura el servidor DNS preferido (p. ej., en systemd-resolved o resolv.conf) para que las consultas se envíen al servidor BIND9 del laboratorio.
:::


## 25. Pruebas con `dig`, `host` y `nslookup`

### Consulta de registro A

```bash
dig @192.168.56.10 www.techserve.test A
```

Debes obtener algo parecido a:

```text
www.techserve.test. 86400 IN A 192.168.56.30
```

### Consulta MX

```bash
dig @192.168.56.10 techserve.test MX
```

Resultado esperado:

```text
techserve.test. 86400 IN MX 10 mail.techserve.test.
```

### Consulta NS

```bash
dig @192.168.56.10 techserve.test NS
```

### Consulta inversa

```bash
dig @192.168.56.10 -x 192.168.56.30
```

Resultado esperado:

```text
30.56.168.192.in-addr.arpa. 86400 IN PTR www.techserve.test.
```

### Usando `host`

```bash
host www.techserve.test 192.168.56.10
host 192.168.56.30 192.168.56.10
```

### Usando `nslookup`

```bash
nslookup www.techserve.test 192.168.56.10
nslookup -type=mx techserve.test 192.168.56.10
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-tools-dig-nslookup
:type: mcq
:n: 2
:difficulty: media
:objective: Usar herramientas de consulta DNS

Herramientas como dig, host y nslookup permiten consultar registros específicos (A, MX, NS, PTR) y diagnosticar si la respuesta es autoritativa, recursiva o cacheada.
:::


## 26. Servidor secundario BIND9

En un segundo servidor Linux, por ejemplo `192.168.56.20`, podríamos crear una zona secundaria.

Archivo:

```text
/etc/bind/named.conf.local
```

Ejemplo:

```text
zone "techserve.test" {
    type secondary;
    primaries { 192.168.56.10; };
    file "/var/cache/bind/db.techserve.test";
};

zone "56.168.192.in-addr.arpa" {
    type secondary;
    primaries { 192.168.56.10; };
    file "/var/cache/bind/db.192.168.56";
};
```

En versiones o documentación antigua de BIND puede aparecer:

```text
type slave;
masters { 192.168.56.10; };
```

La idea es la misma: el servidor secundario obtiene la zona desde el primario.

Comprobación desde el servidor secundario:

```bash
dig @192.168.56.20 www.techserve.test A
```

Comprobar transferencia completa:

```bash
dig @192.168.56.10 techserve.test AXFR
```

Esta última consulta solo debería funcionar desde servidores autorizados.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: bind-secondary
:type: mcq
:n: 2
:difficulty: media
:objective: Configurar servidor secundario BIND9

Un servidor DNS secundario replica una zona desde el primario mediante transferencias autorizadas; en BIND9 se declara la zona como slave y se indica el master.
:::


# Parte práctica: Windows Server DNS


## 27. Instalación del rol DNS en Windows Server

En Windows Server podemos instalar DNS desde:

```text
Administrador del servidor → Agregar roles y características → Servidor DNS
```

También puede hacerse con PowerShell:

```powershell
Install-WindowsFeature DNS -IncludeManagementTools
```

Comprobar el servicio:

```powershell
Get-Service DNS
```

Abrir la consola:

```text
Herramientas → DNS
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: win-dns-install-role
:type: mcq
:n: 2
:difficulty: media
:objective: Instalar el rol DNS en Windows Server

En Windows Server, el rol DNS se instala desde Server Manager y permite administrar zonas, registros, reenviadores y resolución inversa con herramientas gráficas.
:::


## 28. Crear una zona directa en Windows Server

Desde la consola DNS:

```text
DNS Manager → Servidor → Zonas de búsqueda directa → Nueva zona
```

Pasos habituales:

1. Elegir **Zona primaria**.
2. Nombre de zona: `techserve.test`.
3. Crear un nuevo archivo de zona.
4. Elegir si se permiten actualizaciones dinámicas.
5. Finalizar.

Crear registros:

| Registro | Nombre | IP/Destino |
|---|---|---|
| Host A | `ns2` | `192.168.56.20` |
| Host A | `www` | `192.168.56.30` |
| Host A | `mail` | `192.168.56.40` |
| Alias CNAME | `ftp` | `www.techserve.test` |
| MX | `@` | `mail.techserve.test` |

Con PowerShell, algunos ejemplos:

```powershell
Add-DnsServerPrimaryZone -Name "techserve.test" -ZoneFile "techserve.test.dns"
Add-DnsServerResourceRecordA -ZoneName "techserve.test" -Name "www" -IPv4Address "192.168.56.30"
Add-DnsServerResourceRecordA -ZoneName "techserve.test" -Name "mail" -IPv4Address "192.168.56.40"
Add-DnsServerResourceRecordCName -ZoneName "techserve.test" -Name "ftp" -HostNameAlias "www.techserve.test"
Add-DnsServerResourceRecordMX -ZoneName "techserve.test" -MailExchange "mail.techserve.test" -Preference 10
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: win-forward-zone
:type: mcq
:n: 2
:difficulty: media
:objective: Crear zona directa en Windows Server DNS

Una zona directa en Windows Server se crea para un dominio y se añaden registros (A, CNAME, MX, etc.) para resolver nombres a direcciones IP.
:::


## 29. Crear una zona inversa en Windows Server

Desde la consola DNS:

```text
Zonas de búsqueda inversa → Nueva zona
```

Pasos:

1. Elegir zona primaria.
2. Elegir IPv4.
3. Indicar el ID de red: `192.168.56`.
4. Crear el archivo de zona.
5. Finalizar.

Crear registros PTR:

| IP | Nombre |
|---|---|
| `192.168.56.20` | `ns2.techserve.test` |
| `192.168.56.30` | `www.techserve.test` |
| `192.168.56.40` | `mail.techserve.test` |

Con PowerShell:

```powershell
Add-DnsServerPrimaryZone -NetworkID "192.168.56.0/24" -ZoneFile "56.168.192.in-addr.arpa.dns"
Add-DnsServerResourceRecordPtr -ZoneName "56.168.192.in-addr.arpa" -Name "30" -PtrDomainName "www.techserve.test"
Add-DnsServerResourceRecordPtr -ZoneName "56.168.192.in-addr.arpa" -Name "40" -PtrDomainName "mail.techserve.test"
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: win-reverse-zone
:type: mcq
:n: 2
:difficulty: media
:objective: Crear zona inversa en Windows Server DNS

Una zona inversa en Windows Server se crea para un rango de red y permite resolver IP a nombre mediante registros PTR.
:::


## 30. Consultas desde Windows

### `nslookup`

```powershell
nslookup www.techserve.test 192.168.56.20
nslookup -type=mx techserve.test 192.168.56.20
nslookup 192.168.56.30 192.168.56.20
```

### `Resolve-DnsName`

```powershell
Resolve-DnsName www.techserve.test -Server 192.168.56.20
Resolve-DnsName techserve.test -Type MX -Server 192.168.56.20
Resolve-DnsName 192.168.56.30 -Server 192.168.56.20
```

### Ver caché DNS del cliente

```powershell
Get-DnsClientCache
```

Limpiar caché DNS del cliente:

```powershell
Clear-DnsClientCache
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: win-queries
:type: mcq
:n: 2
:difficulty: media
:objective: Realizar consultas DNS desde Windows

Desde Windows se pueden realizar consultas y diagnósticos con nslookup, especificando el servidor DNS y el tipo de registro para verificar la resolución.
:::


## 31. Reenviadores en Windows Server DNS

Desde la consola DNS:

```text
DNS Manager → botón derecho sobre el servidor → Propiedades → Reenviadores
```

Añadir, por ejemplo:

```text
1.1.1.1
8.8.8.8
```

Con PowerShell:

```powershell
Set-DnsServerForwarder -IPAddress 1.1.1.1,8.8.8.8
Get-DnsServerForwarder
```

También existen **reenviadores condicionales**, que permiten reenviar solo las consultas de un dominio concreto a servidores específicos.


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: win-forwarders
:type: mcq
:n: 2
:difficulty: media
:objective: Configurar reenviadores en Windows Server DNS

Los reenviadores en Windows Server DNS permiten remitir consultas externas a un DNS upstream (por ejemplo, el del ISP o uno público) para resolver nombres fuera de la zona local.
:::


# Diagnóstico y resolución de problemas


## 32. Método de diagnóstico paso a paso

Cuando DNS no funciona, no conviene cambiar cosas al azar. Sigue un método.

### 1. Comprobar conectividad IP

```bash
ping 192.168.56.10
```

Si no hay conectividad IP, DNS no es el primer problema.

### 2. Comprobar que el servicio escucha en el puerto 53

Linux:

```bash
sudo ss -tulpn | grep :53
```

Windows:

```powershell
Get-Service DNS
```

### 3. Consultar directamente al servidor DNS

```bash
dig @192.168.56.10 www.techserve.test A
```

Si esto funciona, el servidor responde bien.

### 4. Comprobar la configuración DNS del cliente

Linux:

```bash
resolvectl status
```

Windows:

```powershell
ipconfig /all
```

### 5. Comprobar zona y registros

BIND:

```bash
sudo named-checkzone techserve.test /etc/bind/zones/db.techserve.test
```

### 6. Revisar logs

BIND:

```bash
sudo journalctl -u bind9 -xe
```

Windows:

```text
Visor de eventos → Registros de aplicaciones y servicios → DNS Server
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-diagnosis-method
:type: mcq
:n: 2
:difficulty: media
:objective: Aplicar un método de diagnóstico

Un diagnóstico DNS sistemático comprueba conectividad, configuración de cliente, respuesta del servidor, logs y herramientas (dig/nslookup) para aislar el punto de fallo.
:::


## 33. Errores frecuentes en prácticas

| Error | Síntoma | Solución |
|---|---|---|
| Olvidar el punto final en FQDN | Nombres duplicados o extraños | Revisar registros `NS`, `MX`, `CNAME`, `PTR`. |
| No aumentar el serial | El secundario no actualiza | Incrementar serial y recargar zona. |
| Puerto 53 bloqueado | El cliente no recibe respuesta | Revisar firewall. |
| IP incorrecta en el cliente | El cliente consulta otro DNS | Revisar `ipconfig /all` o `resolvectl status`. |
| Zona inversa mal nombrada | Falla `dig -x` | Revisar orden invertido de octetos. |
| Recursión abierta | Riesgo de abuso externo | Limitar `allow-recursion`. |
| Transferencias abiertas | Exposición de información | Limitar `allow-transfer`. |
| CNAME usado incorrectamente | Resoluciones ambiguas | No mezclar CNAME con otros registros del mismo nombre. |


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-common-errors
:type: mcq
:n: 2
:difficulty: media
:objective: Identificar errores frecuentes en prácticas DNS

Errores frecuentes incluyen serial SOA no actualizado, registros mal escritos, zonas mal declaradas, permisos de ficheros de zona incorrectos y firewall bloqueando el puerto 53.
:::


## 34. Comandos imprescindibles

### Linux

```bash
# Consultar registro A
dig www.techserve.test A

# Consultar a un DNS concreto
dig @192.168.56.10 www.techserve.test A

# Consultar MX
dig techserve.test MX

# Consulta inversa
dig -x 192.168.56.30

# Ver la traza de resolución
dig +trace www.example.com

# Comprobar zona BIND
sudo named-checkzone techserve.test /etc/bind/zones/db.techserve.test

# Ver DNS configurados
resolvectl status
```

### Windows

```powershell
# Configuración IP y DNS
ipconfig /all

# Consulta básica
nslookup www.techserve.test 192.168.56.20

# Consulta avanzada
Resolve-DnsName www.techserve.test -Server 192.168.56.20

# Consultar MX
Resolve-DnsName techserve.test -Type MX -Server 192.168.56.20

# Ver caché DNS
Get-DnsClientCache

# Limpiar caché DNS
Clear-DnsClientCache
```


:::{admonition} Semilla de evaluación (qseed)
:class: qseed
:id: dns-essential-commands
:type: mcq
:n: 2
:difficulty: media
:objective: Enumerar comandos imprescindibles de administración DNS

Comandos como dig, host, nslookup, named-checkconf, named-checkzone, systemctl status bind9 y journalctl ayudan a verificar estado, consultas y errores de BIND9.
:::


# Actividades de aula


## 35. Actividad 1: investigación guiada

Responde brevemente:

1. ¿Qué diferencia hay entre una consulta recursiva y una iterativa?
2. ¿Qué es un servidor autoritativo?
3. ¿Qué diferencia hay entre un registro `A` y un `CNAME`?
4. ¿Para qué sirve un registro `MX`?
5. ¿Por qué es importante el TTL?
6. ¿Qué es una zona inversa?
7. ¿Qué riesgos tiene permitir transferencias de zona a cualquier IP?
8. ¿Por qué no es recomendable dejar la recursión abierta a Internet?


## 36. Actividad 2: análisis de consultas reales

Ejecuta estas consultas y explica qué devuelve cada una:

```bash
dig example.com A
```

```bash
dig example.com MX
```

```bash
dig example.com NS
```

```bash
dig +trace www.example.com
```

Para cada consulta, documenta:

- Comando utilizado.
- Captura o salida relevante.
- Tipo de registro consultado.
- Interpretación del resultado.


## 37. Actividad 3: práctica guiada BIND9

Configura un servidor BIND9 que resuelva la zona `techserve.test`.

Debe incluir:

1. Zona directa.
2. Zona inversa.
3. Registros `A` para `ns1`, `www` y `mail`.
4. Registro `CNAME` para `ftp`.
5. Registro `MX` para el correo.
6. Reenviadores DNS.
7. Pruebas desde un cliente.

### Evidencias mínimas

Incluye en tu memoria:

- Captura o contenido de `named.conf.options`.
- Captura o contenido de `named.conf.local`.
- Archivo de zona directa.
- Archivo de zona inversa.
- Resultado de `named-checkconf`.
- Resultado de `named-checkzone`.
- Consultas `dig` funcionando.
- Consulta inversa funcionando.
- Comprobación desde un cliente distinto al servidor.

> **Criterio práctico:** si el servicio no funciona y no puedes demostrar la resolución desde un cliente, la práctica no puede considerarse completa.


## 38. Actividad 4: DNS en Windows Server

Configura Windows Server DNS para la zona `techserve.test`.

Debe incluir:

1. Instalación del rol DNS.
2. Creación de zona directa.
3. Creación de zona inversa.
4. Registros `A`, `CNAME`, `MX` y `PTR`.
5. Reenviadores.
6. Pruebas desde Windows con `nslookup` y `Resolve-DnsName`.

### Evidencias mínimas

- Captura del rol DNS instalado.
- Captura de la zona directa.
- Captura de la zona inversa.
- Captura de registros creados.
- Salida de `Resolve-DnsName`.
- Salida de `nslookup`.
- Prueba desde un cliente.


## 39. Actividad 5: transferencia de zona

Configura un servidor DNS secundario para `techserve.test`.

Puedes hacerlo de dos formas:

- Primario en Ubuntu + secundario en Windows Server.
- Primario en Ubuntu + secundario en otro Ubuntu Server.

### Debes demostrar

1. Que el primario permite transferencias solo al secundario.
2. Que el secundario recibe la zona.
3. Que el secundario responde consultas.
4. Que al modificar la zona en el primario y aumentar el serial, el secundario acaba actualizándose.
5. Que un equipo no autorizado no puede hacer `AXFR`.

Comando útil:

```bash
dig @192.168.56.10 techserve.test AXFR
```


## 40. Actividad 6: resolución de averías

El profesor puede preparar una máquina con errores intencionados. El alumnado debe diagnosticar y corregirlos.

Ejemplos de averías:

1. Serial no actualizado.
2. Error de sintaxis en archivo de zona.
3. Registro `MX` apuntando a un nombre inexistente.
4. Zona inversa mal escrita.
5. Cliente usando un DNS incorrecto.
6. Firewall bloqueando puerto 53.
7. Recursión no permitida para la red del cliente.
8. Transferencia de zona no autorizada al secundario.

Para cada avería, documenta:

- Síntoma observado.
- Comando utilizado para diagnosticar.
- Causa del problema.
- Solución aplicada.
- Prueba final de funcionamiento.


# Evaluación


## 41. Rúbrica orientativa para una práctica DNS

| Apartado | Puntuación | Descripción |
|---|---:|---|
| Diseño del escenario | 1 punto | IPs, dominio, máquinas y roles bien definidos. |
| Instalación del servicio DNS | 1 punto | Servicio instalado y activo. |
| Zona directa | 1,5 puntos | Registros correctos: `SOA`, `NS`, `A`, `CNAME`, `MX`. |
| Zona inversa | 1 punto | Registros `PTR` correctos. |
| Reenviadores/caché | 1 punto | Resolución interna y externa bien planteada. |
| Pruebas de funcionamiento | 2 puntos | Consultas desde servidor y cliente con evidencias. |
| Seguridad básica | 1 punto | Recursión y transferencias restringidas. |
| Documentación | 1,5 puntos | Explicaciones claras, capturas relevantes y conclusiones. |

Total: **10 puntos**.

### Penalizaciones habituales

- No demostrar funcionamiento desde cliente: penalización importante.
- Aportar capturas sin explicación: reduce la nota de documentación.
- Copiar configuraciones sin adaptarlas al escenario: reduce diseño y documentación.
- No incluir evidencias de comandos: reduce pruebas de funcionamiento.


## 42. Preguntas de repaso

1. ¿Qué significa DNS?
2. ¿Qué es un FQDN?
3. ¿Qué representa el punto final en `www.techserve.test.`?
4. ¿Qué diferencia hay entre zona directa e inversa?
5. ¿Qué registro se usa para resolver IPv4?
6. ¿Qué registro se usa para resolver IPv6?
7. ¿Qué registro se usa para correo electrónico?
8. ¿Qué registro permite crear un alias?
9. ¿Qué registro se usa en resolución inversa?
10. ¿Qué es el TTL?
11. ¿Por qué es importante aumentar el serial?
12. ¿Qué diferencia hay entre servidor recursivo y autoritativo?
13. ¿Para qué sirven los reenviadores?
14. ¿Qué es una transferencia de zona?
15. ¿Qué diferencia hay entre `AXFR` e `IXFR`?
16. ¿Por qué no se deben permitir transferencias de zona a cualquier IP?
17. ¿Qué comando usarías en Linux para comprobar un registro `MX`?
18. ¿Qué comando usarías en Windows para consultar DNS?
19. ¿Qué archivo principal se usa para declarar zonas en BIND9?
20. ¿Qué herramienta permite comprobar la sintaxis de una zona BIND?


## 43. Autoevaluación interactiva opcional

La siguiente celda permite comprobar algunas respuestas de forma automática. Es una actividad sencilla para repasar conceptos.


```python
# Autoevaluación rápida sobre DNS
# Escribe tus respuestas en minúsculas dentro del diccionario.

respuestas = {
    1: "",  # Registro para IPv4: a / aaaa / mx / ptr
    2: "",  # Registro para IPv6: a / aaaa / mx / ptr
    3: "",  # Registro de correo: a / cname / mx / ptr
    4: "",  # Registro de resolución inversa: a / aaaa / mx / ptr
    5: "",  # Herramienta típica en Linux: dig / ping / cd / mkdir
}

soluciones = {
    1: "a",
    2: "aaaa",
    3: "mx",
    4: "ptr",
    5: "dig",
}

puntuacion = 0
for numero, correcta in soluciones.items():
    if respuestas[numero].strip().lower() == correcta:
        print(f"Pregunta {numero}: correcta")
        puntuacion += 1
    else:
        print(f"Pregunta {numero}: incorrecta. Respuesta correcta: {correcta}")

print(f"\nPuntuación: {puntuacion}/{len(soluciones)}")
```

## 44. Plantilla de documentación para el alumnado

Puedes usar esta estructura para entregar la práctica:

```text
1. Portada
   - Nombre del alumno/a
   - Módulo
   - Título de la práctica
   - Fecha

2. Objetivo de la práctica
   - Qué se pretende configurar y demostrar.

3. Escenario de red
   - Tabla de máquinas, IPs, roles y sistema operativo.
   - Diagrama de red.

4. Instalación del servicio DNS
   - Pasos realizados.
   - Evidencias.

5. Configuración de zona directa
   - Archivo o capturas.
   - Explicación de registros.

6. Configuración de zona inversa
   - Archivo o capturas.
   - Explicación de registros PTR.

7. Reenviadores y caché
   - Configuración aplicada.
   - Pruebas de resolución externa.

8. Pruebas de funcionamiento
   - Consultas desde servidor.
   - Consultas desde cliente.
   - Consulta directa e inversa.
   - Registro MX.

9. Seguridad básica
   - Restricción de recursión.
   - Restricción de transferencia de zona.

10. Problemas encontrados y solución
   - Error observado.
   - Diagnóstico.
   - Solución.

11. Conclusión
   - Qué has aprendido.
   - Qué mejorarías.
```


## 45. Glosario básico

| Término | Definición |
|---|---|
| DNS | Sistema de nombres de dominio. |
| FQDN | Nombre de dominio completamente cualificado. |
| Zona | Parte del espacio DNS administrada por un servidor. |
| Registro | Entrada de información dentro de una zona. |
| Autoritativo | Servidor que tiene la información oficial de una zona. |
| Recursivo | Servidor que busca la respuesta completa para un cliente. |
| Reenviador | DNS al que se envían consultas no resueltas localmente. |
| TTL | Tiempo que una respuesta puede permanecer en caché. |
| SOA | Registro de inicio de autoridad de una zona. |
| PTR | Registro utilizado para resolución inversa. |
| AXFR | Transferencia completa de zona. |
| IXFR | Transferencia incremental de zona. |
| DNSSEC | Extensiones de seguridad para validar respuestas DNS. |
| TSIG | Mecanismo de autenticación para transferencias o actualizaciones DNS. |


## 46. Referencias y documentación recomendada

- RFC 1034: *Domain Names - Concepts and Facilities*.
- RFC 1035: *Domain Names - Implementation and Specification*.
- ISC BIND 9 Documentation: *BIND 9 Administrator Reference Manual*.
- Microsoft Learn: *DNS Server en Windows Server*.
- Microsoft Learn: *DNS forwarding in Windows Server*.

Estas referencias son útiles para ampliar información o resolver dudas sobre detalles concretos de configuración.
