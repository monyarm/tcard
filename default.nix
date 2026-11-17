{ lib, stdenvNoCC, python3 }:

let
  version = "0.1.0";

  tests = stdenvNoCC.mkDerivation {
    pname = "tcard-tests";
    inherit version;
    src = lib.cleanSource ./.;
    dontBuild = true;
    doCheck = true;
    checkPhase = ''
      runHook preCheck
      PYTHONPATH="$PWD" ${python3}/bin/python3 tests/run.py
      runHook postCheck
    '';
    installPhase = "touch $out";
  };
in
stdenvNoCC.mkDerivation {
  pname = "tcard";
  inherit version;
  src = lib.cleanSource ./.;
  dontBuild = true;

  installPhase = ''
    mkdir -p $out/bin $out/lib
    cp -r tcard $out/lib/tcard
    printf '#!%s/bin/python3\n' "${python3}" > $out/bin/tcard
    printf 'import sys\nsys.path.insert(0, "%s/lib")\nfrom tcard.cli import main\nraise SystemExit(main())\n' "$out" >> $out/bin/tcard
    chmod +x $out/bin/tcard
  '';

  passthru.tests = tests;

  meta = {
    description = "Tabletop cards on stdout, sized for a 58 mm thermal printer";
    mainProgram = "tcard";
    platforms = lib.platforms.linux;
  };
}
