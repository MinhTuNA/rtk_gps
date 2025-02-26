import math


def WGS_to_ECEF(lat, lon, alt):
    """
    Chuyển đổi từ WGS84 (lat, lon, alt) sang ECEF (X, Y, Z)

    :param lat: Latitude (độ)
    :param lon: Longitude (độ)
    :param alt: Độ cao so với ellipsoid WGS84 (m)
    :return: (X, Y, Z) tọa độ ECEF
    """
    # Hằng số WGS84
    a = 6378137.0  # Bán trục lớn (m)
    e_sq = 6.69437999014 * 10**-3  # Độ lệch tâm bình phương

    # Chuyển đổi sang radian
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    # Tính bán kính cong N
    N = a / math.sqrt(1 - e_sq * math.sin(lat_rad)**2)

    # Tọa độ ECEF
    X = (N + alt) * math.cos(lat_rad) * math.cos(lon_rad)
    Y = (N + alt) * math.cos(lat_rad) * math.sin(lon_rad)
    Z = ((1 - e_sq) * N + alt) * math.sin(lat_rad)

    return X, Y, Z


def ECEF_to_WGS84(x=None, y=None, z=None, tolerance=1e-12):
    a = 6378137.0
    e2 = 0.00669438

    # kinh độ
    _lon = math.atan2(y, x)
    # khoảng cách p trên mặt phẳng x y
    p = math.sqrt(x**2 + y**2)
    # ước tính ban đầu cho vĩ độ
    fi0 = math.atan2(z, p*(1-e2))

    while True:
        sin_fi = math.sin(fi0)
        N = a / math.sqrt(1-e2*sin_fi**2)
        new_fi = math.atan2(z+e2*N*sin_fi, p)
        if abs(new_fi - fi0) < tolerance:
            fi = new_fi
            break
        fi0 = new_fi

    N = a/math.sqrt(1 - e2*math.sin(fi)**2)
    # độ cao
    alt = p/math.cos(fi)-N

    lat = math.degrees(fi)
    lon = math.degrees(_lon)

    return lat, lon, alt


if __name__ == "__main__":
    x_cm = -191916192
    y_cm = 582136804
    z_cm = 175738933

    # Chuyển sang mét
    x = (x_cm + (-44 * 0.01)) * 0.01
    y = (y_cm + (7 * 0.01)) * 0.01
    z = (z_cm + (-1 * 0.01)) * 0.01

    lat, lon, alt = ECEF_to_WGS84(x, y, z)
    print(f"Vĩ độ: {lat:.6f}°")
    print(f"Kinh độ: {lon:.6f}°")
    print(f"Độ cao: {alt} m")

    # lat = 16.100324
    # lon = 108.246136
    X, Y, Z = WGS_to_ECEF(lat, lon, alt)
    print(f"X: {X:.2f} m")
    print(f"Y: {Y:.2f} m")
    print(f"Z: {Z:.2f} m")
