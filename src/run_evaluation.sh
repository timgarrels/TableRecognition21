# Run Evaluations


# ----- FusTe -----
# With noise
python3 src/run_cross_validation.py --dataset FusTe --noise --seed 1 --threads 10 &> fuste_noise_1 &
python3 src/run_cross_validation.py --dataset FusTe --noise --seed 2 --threads 10 &> fuste_noise_2 &
python3 src/run_cross_validation.py --dataset FusTe --noise --seed 3 --threads 10 &> fuste_noise_3 &
# Without noise
python3 src/run_cross_validation.py --dataset FusTe --seed 1 --threads 10 &> fuste_no_noise_1 &
python3 src/run_cross_validation.py --dataset FusTe --seed 2 --threads 10 &> fuste_no_noise_2 &
python3 src/run_cross_validation.py --dataset FusTe --seed 3 --threads 10 &> fuste_no_noise_3 &

# ----- Deco -----
# With noise
python3 src/run_cross_validation.py --dataset Deco --noise --seed 1 --threads 10 &> deco_noise_1 &
python3 src/run_cross_validation.py --dataset Deco --noise --seed 2 --threads 10 &> deco_noise_2 &
python3 src/run_cross_validation.py --dataset Deco --noise --seed 3 --threads 10 &> deco_noise_3 &
# Without noise
python3 src/run_cross_validation.py --dataset Deco --seed 1 --threads 10 &> deco_no_noise_1 &
python3 src/run_cross_validation.py --dataset Deco --seed 2 --threads 10 &> deco_no_noise_2 &
python3 src/run_cross_validation.py --dataset Deco --seed 3 --threads 10 &> deco_no_noise_3 &