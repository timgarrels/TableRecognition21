# Run Evaluations


# ----- FusTe -----
# With noise
python3 src/run_cross_validation.py --dataset FusTe --noise --seed 1 2&>1 > fuste_noise_1 &
python3 src/run_cross_validation.py --dataset FusTe --noise --seed 2 &> fuste_noise_2 &
python3 src/run_cross_validation.py --dataset FusTe --noise --seed 3 &> fuste_noise_3 &
# Without noise
python3 src/run_cross_validation.py --dataset FusTe --seed 1 &> fuste_no_noise_1 &
python3 src/run_cross_validation.py --dataset FusTe --seed 2 &> fuste_no_noise_2 &
python3 src/run_cross_validation.py --dataset FusTe --seed 3 &> fuste_no_noise_3 &

# ----- Deco -----
# With noise
python3 src/run_cross_validation.py --dataset Deco --noise --seed 1 &> deco_noise_1 &
python3 src/run_cross_validation.py --dataset Deco --noise --seed 2 &> deco_noise_2 &
python3 src/run_cross_validation.py --dataset Deco --noise --seed 3 &> deco_noise_3 &
# Without noise
python3 src/run_cross_validation.py --dataset Deco --seed 1 &> deco_no_noise_1 &
python3 src/run_cross_validation.py --dataset Deco --seed 2 &> deco_no_noise_2 &
python3 src/run_cross_validation.py --dataset Deco --seed 3 &> deco_no_noise_3 &