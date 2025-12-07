# pogodynka-rpizero

## Po zmianie
* docker build -t weather-station-weather .

## Uruchamianie


* docker rm -f weather-station-rumia || true

docker run -d \
  --name weather-station-rumia \
  -p 5080:5080 \
  --device /dev/i2c-1 \
  --device /dev/gpiomem \
  weather-station-weather

