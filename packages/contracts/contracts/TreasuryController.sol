// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { SD59x18, sd } from "@prb/math/src/SD59x18.sol";
import { UD60x18, ud } from "@prb/math/src/UD60x18.sol";

/**
 * @title TreasuryController
 * @notice Implements a PID Controller to dynamically adjust burn and recycle rates based on token price stability.
 * @dev Uses PRBMath (SD59x18) for fixed-point arithmetic to handle negative errors and integral accumulation.
 */
contract TreasuryController is AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant KEEPER_ROLE = keccak256("KEEPER_ROLE");

    // --- PID Control Variables (SD59x18 for signed math) ---
    SD59x18 public kp;
    SD59x18 public ki;
    SD59x18 public kd;

    SD59x18 public integral;
    SD59x18 public prevError;

    // --- State Variables ---
    UD60x18 public targetPrice; // USD value (e.g., 50.0)
    uint256 public lastEpochTime;
    uint256 public epochDuration; // e.g., 3600 seconds (1 hour)

    // --- Output Rates (Percentage 0-100, encoded as UD60x18) ---
    UD60x18 public burnRate;
    UD60x18 public recycleRate;

    // --- Events ---
    event RatesUpdated(uint256 burnRate, uint256 recycleRate);
    event CoefficientsUpdated(int256 kp, int256 ki, int256 kd);
    event EpochUpdated(uint256 timestamp, int256 error, int256 output);

    // --- Errors ---
    error EpochNotFinished();

    constructor(address _admin, uint256 _targetPrice, uint256 _epochDuration) {
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(ADMIN_ROLE, _admin);
        
        targetPrice = ud(_targetPrice); // e.g., 50 * 1e18
        epochDuration = _epochDuration;
        lastEpochTime = block.timestamp;

        // Default coefficients optimized via Agent-Gym Simulation (Phase 5.1)
        // Scaled down by 10x to match simulation's output mapping (0.1 factor)
        // Sim Best: Kp=0.5, Ki=0.01, Kd=0.05 -> Contract: Kp=0.05, Ki=0.001, Kd=0.005
        kp = sd(5e16);   // 0.05
        ki = sd(1e15);   // 0.001
        kd = sd(5e15);   // 0.005
        
        // Initial rates: 50/50 split
        burnRate = ud(5e17); // 0.5 (50%)
        recycleRate = ud(5e17); // 0.5 (50%)
    }

    /**
     * @notice Updates the PID loop and calculates new rates.
     * @dev Should be called by a Keeper or automated script every epoch.
     * @param currentPrice The current DAIM/USD price from Oracle (18 decimals).
     */
    function updateEpoch(uint256 currentPrice) external {
        if (block.timestamp < lastEpochTime + epochDuration) revert EpochNotFinished();

        // 1. Calculate Error (Target - Current)
        // If Price < Target (Undervalued) -> Error > 0 -> Output > 0 -> Increase Burn (Deflation)
        // If Price > Target (Overvalued)  -> Error < 0 -> Output < 0 -> Decrease Burn (Inflation/Recycle)
        SD59x18 price = sd(int256(currentPrice));
        SD59x18 target = sd(int256(targetPrice.unwrap()));
        SD59x18 error = target.sub(price);

        // 2. Calculate DT (Time delta)
        int256 dtInt = int256(block.timestamp - lastEpochTime);
        // Avoid division by zero if called in same block (guarded by logic check but safe to add)
        if (dtInt == 0) dtInt = 1;
        SD59x18 dt = sd(dtInt * 1e18); // Convert Int to SD59x18

        // 3. Update Integral with Windup Guard
        // integral += error * dt
        SD59x18 errorIntegral = error.mul(dt);
        integral = integral.add(errorIntegral);

        // Windup Guard: Cap integral to prevent runaway effect
        // Cap absolute value at 1000 (roughly 20x target price range)
        SD59x18 maxIntegral = sd(1000e18);
        SD59x18 minIntegral = sd(-1000e18);
        if (integral.unwrap() > maxIntegral.unwrap()) integral = maxIntegral;
        if (integral.unwrap() < minIntegral.unwrap()) integral = minIntegral;

        // 4. Calculate Derivative
        // derivative = (error - prevError) / dt
        SD59x18 derivative = (error.sub(prevError)).div(dt);
        prevError = error;

        // 5. Compute PID Output
        // output = (Kp * error) + (Ki * integral) + (Kd * derivative)
        SD59x18 output = kp.mul(error).add(ki.mul(integral)).add(kd.mul(derivative));

        // 6. Map Output to Rates
        // Base rate is 0.5 (50% burn). Output modifies this.
        // Output > 0 (Price too low) -> Burn Rate increases
        // Output < 0 (Price too high) -> Burn Rate decreases
        SD59x18 base = sd(5e17); // 0.5
        SD59x18 newBurnRate = base.add(output);

        // Clamp Burn Rate between 0.1 (10%) and 0.9 (90%)
        SD59x18 minRate = sd(1e17);
        SD59x18 maxRate = sd(9e17);
        
        if (newBurnRate.unwrap() < minRate.unwrap()) newBurnRate = minRate;
        if (newBurnRate.unwrap() > maxRate.unwrap()) newBurnRate = maxRate;

        // Update State
        // Cast SD to UD for storage (we know it's positive due to clamping)
        burnRate = ud(uint256(newBurnRate.unwrap()));
        recycleRate = ud(1e18).sub(burnRate); // 1.0 - BurnRate

        lastEpochTime = block.timestamp;
        
        emit EpochUpdated(block.timestamp, error.unwrap(), output.unwrap());
        emit RatesUpdated(burnRate.unwrap(), recycleRate.unwrap());
    }

    /**
     * @notice Admin function to tune PID coefficients.
     * @dev Helps adjust system sensitivity as market matures.
     */
    function updateCoefficients(int256 _kp, int256 _ki, int256 _kd) external onlyRole(ADMIN_ROLE) {
        kp = sd(_kp);
        ki = sd(_ki);
        kd = sd(_kd);
        emit CoefficientsUpdated(_kp, _ki, _kd);
    }

    /**
     * @notice Getter for current rates.
     */
    function getRates() external view returns (uint256, uint256) {
        return (burnRate.unwrap(), recycleRate.unwrap());
    }
}
