{pkgs}: {
  deps = [
    pkgs.zlib
    pkgs.xcodebuild
    pkgs.cacert
    pkgs.mbedtls_2
    pkgs.postgresql
    pkgs.openssl
  ];
}
